# MediathekViewBot
## What does it try to do?
MediathekViewBot is a Python CLI program that tries its best to find films in the libraries of the german public broadcasting companies using the MediathekView API. 
It then searches the found titles in "The Movie Database" (TMDB) and gets their rating and popularity. 
If the rating and popularity are above a configurable threshold, it generates a text file with the direct links to the videos streams. 
The file of links can be used with programs such as yt-dlp to download the videos. 

## 
