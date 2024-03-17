import concurrent.futures
import tiktoken
from groq import Groq
import sys
import re
import os

def extract_video_id(video_url):
    regex = r"(?:v=|\/|embed\/|shorts\/|v\/|e\/|watch\?v=|\&v=)([^#\&\?]*)"
    match = re.search(regex, video_url)
    return match.group(1) if match else None

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def process_chunk(chunk, max_length, start_time, end_time):
    client = Groq()
    prompt = f"""
    Analyze the following video transcript chunk and identify the most important moments.
    Provide only the timestamps in the format 'HH:MM:SS.mmm --> HH:MM:SS.mmm' for moments between {max_length//2} and {max_length} seconds long, and within the time range from {start_time} to {end_time}.
    The important moments should capture coherent and meaningful segments of the conversation.

    Example:
    Transcript chunk: [Transcript text...]
    Important moments:
    01:30:00.000 --> 01:32:15.000
    01:45:00.000 --> 01:47:30.000

    Transcript chunk:
    {chunk}
    Important moments:
    """

    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    important_moments = []
    current_moment = ""

    for chunk in completion:
        content = chunk.choices[0].delta.content
        if content:
            current_moment += content
        elif current_moment:
            important_moments.append(current_moment.strip())
            current_moment = ""

    if current_moment:
        important_moments.append(current_moment.strip())

    return important_moments

def get_important_moments(video_url, output_file, max_length=180, start_time=None, end_time=None):
    video_id = extract_video_id(video_url)
    if video_id is None:
        print("Error: Unable to extract video ID from the provided URL.")
        return

    transcript_file = os.path.join("videos", video_id, f"{video_id}_transcript.vtt")

    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found: {transcript_file}")
        return

    with open(transcript_file, "r") as f:
        lines = f.readlines()

    transcript = ""
    recording = False

    for line in lines:
        if " --> " in line:
            timestamp_start, timestamp_end = line.strip().split(" --> ")
            if start_time is None or timestamp_start >= start_time:
                recording = True
            if end_time is not None and timestamp_end > end_time:
                recording = False
                break
        elif recording:
            transcript += line.strip() + " "

    max_tokens = 15000
    encoding_name = "cl100k_base"
    chunks = []
    current_chunk = ""

    for word in transcript.split():
        word_tokens = num_tokens_from_string(word, encoding_name)
        if num_tokens_from_string(current_chunk, encoding_name) + word_tokens > max_tokens:
            chunks.append(current_chunk.strip())
            current_chunk = ""
        current_chunk += word + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_chunk, chunk, max_length, start_time, end_time) for chunk in chunks]

        with open(output_file, "w") as f:
            for i, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                important_moments = future.result()
                for moment in important_moments:
                    f.write(moment + "\n")
                print(f"Chunk {i}/{len(chunks)} processed. Important moments written to {output_file}.")

    print(f"All chunks processed. Important moments saved to {output_file}.")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python get_important_moments.py <video_url> <output_file> <start_time> <end_time>")
        sys.exit(1)

    video_url = sys.argv[1]
    output_file = sys.argv[2]
    start_time = sys.argv[3] if sys.argv[3] != "None" else None
    end_time = sys.argv[4] if sys.argv[4] != "None" else None

    get_important_moments(video_url, output_file, start_time=start_time, end_time=end_time)
