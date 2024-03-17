from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import ast
import re
import sys

def extract_video_id(video_url):
    regex = r"(?:v=|\/|embed\/|shorts\/|v\/|e\/|watch\?v=|\&v=)([^#\&\?]*)"
    match = re.search(regex, video_url)
    return match.group(1) if match else None

class Editor:
    def __init__(self, video_path, output_path, important_moments_file, word_boundary_file, duration_threshold=1.0):
        self.video_path = video_path
        self.output_path = output_path
        self.important_moments_file = important_moments_file
        self.word_boundary_file = word_boundary_file
        self.duration_threshold = duration_threshold

    def create_movie(self):
        # Load video clip with audio
        video_clip = VideoFileClip(self.video_path)

        # Load WordBoundary data
        with open(self.word_boundary_file, 'r') as f:
            word_boundaries = [ast.literal_eval(':'.join(line.split(':')[1:]).strip()) for line in f]

        # Read important moments from the text file
        with open(self.important_moments_file, 'r') as f:
            important_moments = [line.strip() for line in f]

        for i, moment in enumerate(important_moments):
            # Extract start and end times from the important moment
            match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})', moment)
            if match:
                start_time = match.group(1)
                end_time = match.group(2)

                # Convert start and end times to seconds
                start_seconds = self.convert_to_seconds(start_time)
                end_seconds = self.convert_to_seconds(end_time)

                # Find the closest matching word boundaries for the moment
                start_boundary = min(word_boundaries, key=lambda x: abs(x['offset'] / 10000000 - start_seconds))
                end_boundary = min(word_boundaries, key=lambda x: abs((x['offset'] + x['duration']) / 10000000 - end_seconds))

                # Create a subclip of the video based on the matching word boundaries
                moment_start = start_boundary['offset'] / 10000000
                moment_end = (end_boundary['offset'] + end_boundary['duration']) / 10000000
                moment_clip = video_clip.subclip(moment_start, moment_end)

                # Find the corresponding word boundaries for the moment
                moment_word_boundaries = [
                    wb for wb in word_boundaries if moment_start <= wb['offset'] / 10000000 <= moment_end
                ]

                subtitles = []
                current_subtitle = ""
                current_start = None
                current_duration = 0

                for word_boundary in moment_word_boundaries:
                    start = word_boundary['offset'] / 10000000  # Convert nanoseconds to seconds
                    duration = word_boundary['duration'] / 10000000  # Convert nanoseconds to seconds
                    text = word_boundary['text']

                    if current_start is None:
                        current_start = start
                    current_subtitle += text + " "
                    current_duration += duration

                    if current_duration >= self.duration_threshold:
                        # Create a TextClip for the current subtitle with yellow color
                        txt_clip = (TextClip(current_subtitle.strip(), fontsize=50, color='yellow', bg_color='Transparent', font='Arial-Bold')
                                    .set_position('center')
                                    .set_duration(current_duration)
                                    .set_start(current_start - moment_start))
                        subtitles.append(txt_clip)
                        current_subtitle = ""
                        current_start = None
                        current_duration = 0

                if current_subtitle:
                    # Create a TextClip for the remaining subtitle with yellow color
                    txt_clip = (TextClip(current_subtitle.strip(), fontsize=50, color='yellow', bg_color='Transparent', font='Arial-Bold')
                                .set_position('center')
                                .set_duration(current_duration)
                                .set_start(current_start - moment_start))
                    subtitles.append(txt_clip)

                # Create a CompositeVideoClip with the video and subtitles
                final_clip = CompositeVideoClip([moment_clip] + subtitles, size=moment_clip.size).set_duration(moment_clip.duration)

                # Write the final clip to the output path with reduced bitrate
                output_file = f"{self.output_path}_{i}.mp4"
                final_clip.write_videofile(output_file, codec='libx264')

    def convert_to_seconds(self, time_str):
        hours, minutes, seconds = time_str.split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python create_movie.py <video_file> <output_file> <important_moments_file> <word_boundary_file>")
        sys.exit(1)

    video_file = sys.argv[1]
    output_file = sys.argv[2]
    important_moments_file = sys.argv[3]
    word_boundary_file = sys.argv[4]

    video_id = extract_video_id(video_file)
    video_file = video_file.replace(video_file.split("/")[-1], f"{video_id}.mp4")

    movie = Editor(video_file, output_file, important_moments_file, word_boundary_file, duration_threshold=1.0)
    movie.create_movie()
