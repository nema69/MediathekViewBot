import subprocess

def downloadMovie(movie, output_path):
    url = movie.get("url_video_hd")
    title = movie.get("title")
    argumentsVideo = ["yt-dlp", url,  "--paths", output_path, "-o", title]
    subprocess.run(argumentsVideo)