#!/usr/bin/env python3

# Classes importing
from yt_dlp import YoutubeDL
import argparse
import sys
import subprocess
from pyfzf.pyfzf import FzfPrompt
import pathlib
import platform

# Initialize fzf
fzf = FzfPrompt()
MUSIC_DIR = pathlib.Path.home() / "Music"

system = platform.system()

if system == "Windows":
    mpv = "mpv.com"
else:
    mpv = "mpv"

# Function for argument parsing
def parse_arguments():

    global args

    parser = argparse.ArgumentParser(
            prog="pl",
            description="Which stands for Play Lofi, Is a simple lofi player that scrapes Youtube for Music",
            add_help=True,
            )
    parser.add_argument('-u', type=str,help='Specify the Youtube URL for the stream')
    parser.add_argument('-m',action='store_true', help="To use mpv instead of vlc")
    parser.add_argument('-q', action='store_true', help="Runs it in quiet mode")
    parser.add_argument('-c', type=str,help='Specify the Youtube Channel URL for listing of streams')
    parser.add_argument('-s', action='store_true', help="Add this to play music on shuffle")
    parser.add_argument('-l', action='store_true', help="Play local files")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

parse_arguments();

# yt-dlp options
ydl_opts = {
            
            'format':"bestaudio/best",
            'noplaylist' : True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': False,
            'verbose': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
}


# A simple function that just gets the url of the youtube video
def get_audio_url(video_url):

    with YoutubeDL(ydl_opts) as ydl:

        info_dict = ydl.extract_info(video_url, download=False)
        audio_url = info_dict["url"]
        return audio_url 

def download_audio(title, video_url):
    opts = ydl_opts.copy()
    opts["outtmpl"] = str(MUSIC_DIR / f"{title}.%(ext)s")
    
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

def play_local_audio():
    files = list(MUSIC_DIR.glob("*.mp3"))

    if not files:
        print("No downloaded songs found.")
        return

    files_names = [f.name for f in files]
    selected = fzf.prompt(files_names)

    if not selected:
        print("No song selected")
        return

    selected_file = MUSIC_DIR / selected[0]
    mpv_player(selected_file)

# Channel Scraper Function
def channel_scraper(channel_url):

    streams = {

        "title": [],
        "url": [],

    } 

    opts = ydl_opts.copy() 
    opts["extract_flat"] = True
    opts["skip_download"] = True
    
    with YoutubeDL(opts) as ydl:
        info_dict = ydl.extract_info(channel_url, download=False)

        entries = info_dict["entries"]

        for entry in entries:
            for video in entry["entries"]:
                title = video.get("title")
                url = video.get("url")
                
                if title and url:
                    streams["title"].append(title)
                    streams["url"].append(url)

    selected_choice = fzf.prompt(streams["title"])

    video_title = selected_choice[0]

    video_index = streams["title"].index(video_title) 

    audio_url = streams['url'][video_index] 
    
    converted_url = get_audio_url(audio_url);

    return converted_url

# Youtube search scrape function
def search_youtube_and_select(query, max_results=5):

    search_query = f"ytsearch{max_results}:{query}"

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)

    streams = {
        "title": [],
        "url": [],
    }

    for entry in info.get("entries", []):
        title = entry.get("title")
        video_id = entry.get("id")
        if title and video_id:
            streams["title"].append(title)
            streams["url"].append(f"https://www.youtube.com/watch?v={video_id}")

    if not streams["title"]:
        print("No results found.")
        return None

    selected_choice = fzf.prompt(streams["title"])
    if not selected_choice:
        return None

    selected_title = selected_choice[0]
    index = streams["title"].index(selected_title)
    selected_url = streams["url"][index]

    audio_url = get_audio_url(selected_url)
    return selected_title, audio_url


# Process for playing mpv player
def mpv_player(audio_url):

    subprocess.run([mpv, "--no-video", audio_url])

# Main function
def main():  
    
    parse_arguments();

    if args.c:
        audio_url = channel_scraper(args.c);

        if args.m:
            mpv_player(audio_url);

    elif args.u:
            
            title, audio_url = search_youtube_and_select(args.u);
            download_audio(title, audio_url)

            if args.m:
                downloaded_file = download_audio(title, audio_url)
                subprocess.run(["mpv", "--no-video", downloaded_file])

    elif args.l:
        play_local_audio()

if __name__ == "__main__":
    main()
