import os
from youtube_transcript_api import YouTubeTranscriptApi
import sys
from pytube import YouTube
import re

def download_video(video_url, quality='720p'):
    video_id = extract_video_id(video_url)
    if video_id is None:
        raise ValueError("Invalid YouTube video URL")

    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")

    # Create the "videos" directory if it doesn't exist
    os.makedirs("videos", exist_ok=True)

    # Get the video stream with the desired quality
    stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=quality).first()
    if stream is None:
        # If the desired quality is not available, select the highest quality below it
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

    # Download the video
    video_file = stream.download(output_path=os.path.join("videos", video_id), filename=f"{video_id}.mp4")

    return video_file, video_id

def extract_video_id(video_url):
    regex = r"(?:v=|\/|embed\/|shorts\/|v\/|e\/|watch\?v=|\&v=)([^#\&\?]*)"
    match = re.search(regex, video_url)
    return match.group(1) if match else None


def get_transcript_with_timestamps(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_with_timestamps = []
    for entry in transcript:
        text = entry['text']
        start = entry['start']
        transcript_with_timestamps.append((text, start))
    return transcript_with_timestamps

def format_timestamp(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def save_transcript_to_file(transcript_with_timestamps, folder_path, filename):
    file_path = os.path.join(folder_path, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        for text, start in transcript_with_timestamps:
            timestamp = format_timestamp(int(start))
            f.write(f'{timestamp}: {text}\n')

def save_transcript_to_vtt(transcript_with_timestamps, folder_path, filename):
    file_path = os.path.join(folder_path, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for i in range(len(transcript_with_timestamps) - 1):
            text, start = transcript_with_timestamps[i]
            _, end = transcript_with_timestamps[i + 1]
            start_time = format_timestamp(int(start)) + ".000"
            end_time = format_timestamp(int(end)) + ".000"
            f.write(f"{start_time} --> {end_time}\n{text}\n\n")

def get_transcript_with_word_timestamps(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_with_word_timestamps = []
    for entry in transcript:
        text = entry['text']
        start = entry['start']
        duration = entry['duration']
        words = text.split()
        word_duration = duration / len(words)
        for i, word in enumerate(words):
            word_start = start + i * word_duration
            word_end = word_start + word_duration
            transcript_with_word_timestamps.append({
                'type': 'WordBoundary',
                'offset': int(word_start * 10**7),
                'duration': int(word_duration * 10**7),
                'text': word
            })
    return transcript_with_word_timestamps

def save_transcript_to_word_timestamp_file(transcript_with_word_timestamps, folder_path, filename):
    file_path = os.path.join(folder_path, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        for word_boundary in transcript_with_word_timestamps:
            f.write(f"WordBoundary: {word_boundary}\n")


def main(video_url, quality='720p'):
    try:
        video_file, video_id = download_video(video_url, quality)
        print(f"Video downloaded: {video_file}")

        transcript_with_timestamps = get_transcript_with_timestamps(video_id)
        if not transcript_with_timestamps:
            print("No transcript found for the given video ID.")
            return

        video_folder = os.path.join("videos", video_id)
        os.makedirs(video_folder, exist_ok=True)

        filename_txt = f"{video_id}_transcript.txt"
        filename_vtt = f"{video_id}_transcript.vtt"
        filename_word_timestamps = f"{video_id}_transcript_word_timestamps.txt"

        save_transcript_to_file(transcript_with_timestamps, video_folder, filename_txt)
        save_transcript_to_vtt(transcript_with_timestamps, video_folder, filename_vtt)

        transcript_with_word_timestamps = get_transcript_with_word_timestamps(video_id)
        save_transcript_to_word_timestamp_file(transcript_with_word_timestamps, video_folder, filename_word_timestamps)

        print(f"Transcript saved to {os.path.join(video_folder, filename_txt)}")
        print(f"VTT subtitle file saved to {os.path.join(video_folder, filename_vtt)}")
        print(f"Transcript with word timestamps saved to {os.path.join(video_folder, filename_word_timestamps)}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python get_transcript.py <video_url> [quality]")
        sys.exit(1)

    video_url = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) == 3 else '720p'

    main(video_url, quality)