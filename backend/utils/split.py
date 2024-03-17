from moviepy.editor import VideoFileClip
import math

def split_video(video_path, output_path, split_length):
    video = VideoFileClip(video_path)
    duration = video.duration

    for i in range(0, math.ceil(duration), split_length):
        start = i
        end = (i + split_length) if (i + split_length) < duration else duration
        subclip = video.subclip(start, end)
        subclip.write_videofile(f"{output_path}/vide2min_{i//split_length}.mp4", codec='libx264')

# Example usage
split_video("minecraft.mp4", "C:/Users/yceta/Escritorio/moneyprinter", 120)

