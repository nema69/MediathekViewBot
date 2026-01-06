import subprocess
from yt_dlp import YoutubeDL

def downloadMovie(movie, outputPath):
    url = movie.get("url_video_hd")
    opts ={
    'outtmpl': f'{outputPath}/{movie.get("title")}.%(ext)s',
    'restrictedfilenames': True,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download(url)

def downloadMovieList(movieList, outputPath):
    for movie in movieList:
        downloadMovie(movie, outputPath)
    
