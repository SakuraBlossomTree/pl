#!/usr/bin/env python3

# Classes importing
from yt_dlp import YoutubeDL
import vlc
import argparse
import sys
import subprocess
from pyfzf.pyfzf import FzfPrompt
import requests
from bs4 import BeautifulSoup
import os 
import json

# Initialize fzf
fzf = FzfPrompt()

# Function for argument parsing
def parse_arguments():

    global args

    parser = argparse.ArgumentParser(
            prog="pl",
            description="Which stands for Play Lofi, Is a simple lofi player that scrapes Youtube and Lofi Girl's Website for Music",
            add_help=True,
            )
    parser.add_argument('-u', type=str,help='Specify the Youtube URL for the stream')
    parser.add_argument('-m',action='store_true', help="To use mpv instead of vlc")
    parser.add_argument('-q', action='store_true', help="Runs it in quiet mode")
    parser.add_argument('-c', type=str,help='Specify the Youtube Channel URL for listing of streams')
    parser.add_argument('-s', action='store_true', help="Add this to play music on shuffle")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

parse_arguments();

# yt-dlp options
ydl_opts = {
            
            'format':"mp3/bestaudio/best",
            'noplaylist' : True,
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'verbose': False,
}


# A simple function that just gets the url of the youtube video
def get_audio_url(video_url):

    with YoutubeDL(ydl_opts) as ydl:

        info_dict = ydl.extract_info(video_url, download=False)
        audio_url = info_dict["url"]
        return audio_url 

# Channel Scraper Function
def channel_scraper(channel_url):

    streams = {

        "title": [],
        "url": [],

    } 

    with YoutubeDL(ydl_opts) as ydl:
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
def search_youtube_and_select(query, max_results=10):

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
    return audio_url


# Process for playing mpv player
def mpv_player(audio_url):

    subprocess.run(["mpv", "--no-video",audio_url])

# Main function
def main():  
    
    parse_arguments();

    if args.c:
        audio_url = channel_scraper(args.c);

        if args.m:
            mpv_player(audio_url);

    elif args.u:
            
            audio_url = search_youtube_and_select(args.u);

            if args.m:
                mpv_player(audio_url);

if __name__ == "__main__":
    main()
