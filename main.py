#!/usr/bin/env python3

# Classes importing
from urllib import request
from yt_dlp import YoutubeDL
import vlc
import argparse
import sys
import subprocess
import json
import ast 
from pyfzf.pyfzf import FzfPrompt
import requests
from bs4 import BeautifulSoup
import time

# Test URL
# LOFI_STREAM_URL = "https://www.youtube.com/watch?v=lTRiuFIWV54"

# LOFI_STREAM_URL = "https://www.youtube.com/watch?v=J2i0cZWCdq4"

LOFI_GIRL_BASE_URL = "https://lofigirl.com/wp-content/uploads/"

fzf = FzfPrompt()

# yt-dlp options
ydl_opts = {

            'format':"mp3/bestaudio/best",
            'noplaylist' : True,
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'verbose': True,
}

# Function for argument parsing
def parse_arguments():

    global args

    parser = argparse.ArgumentParser(
            prog="pl",
            description="Which stands for Play Lofi, Is a simple lofi player that scrapes Youtube for URL",
            add_help=True,
            )
    parser.add_argument('-u', type=str,help='Specify the Youtube URL for the stream')
    parser.add_argument('-m',action='store_true', help="To use mpv instead of vlc")
    parser.add_argument('-q', action='store_true', help="Runs it in quiet mode")
    parser.add_argument('-c', type=str,help='Specify the Youtube Channel URL for listing of streams')
    parser.add_argument('-w', type=int, help="Scrape from Lofi Girl Website")
    
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

# A simple function that just gets the url of the youtube video
def get_audio_url(video_url):

    global audio_url

    with YoutubeDL(ydl_opts) as ydl:
        
        info_dict = ydl.extract_info(video_url, download=False)
        audio_url = info_dict["url"] 
        return audio_url


def channel_scraper(channel_url):

    streams = {

        "title": [],
        "url": [],

    } 

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(channel_url, download=False)

        entries = info_dict["entries"][1]["entries"]

        for i in range(len(entries)):
            url = entries[i]["url"]
            title = entries[i]["title"]

            if title and url:
                streams["title"].append(title)
                streams["url"].append(url)

    # with open('content.txt','w') as f:
    #     json.dump(info_dict,f)

    selected_choice = fzf.prompt(streams["title"])

    video_title = selected_choice[0]

    video_index = streams["title"].index(video_title) 

    print(video_index)

    print(streams['title'][8])

    audio_url = streams['url'][video_index] 

    converted_url = get_audio_url(audio_url);

    return converted_url

# Function to run the audio stream via the vlc player
def vlc_player(audio_url):

    player = vlc.MediaPlayer(audio_url)
    player.play()

    while True:
        pass

def mpv_player_url(audio_url):

    subprocess.run(["mpv", audio_url])

def website_scraper(url):

    # response = requests.get(url)
    #
    # print(response)
    #
    # soup = BeautifulSoup(response.content , "html.parser")
    # 
    # links = soup.find_all("a") 

    # full_url = url + "/01/" 
    #
    # response = requests.get(full_url)
    #
    # soup = BeautifulSoup(response.content, "html.parser")
    #
    # links = soup.find_all("a")
    #
    # mp3_links = [link["href"] for link in links if "href" in link.attrs and link['href'].endswith(".mp3")]
    #
    # for i in range(len(mp3_links)):
    #     with open("playlist.m3u", "a") as f:
    #         f.write("\n"+full_url + mp3_links[i] + "\n")

    with open("playlist.m3u", "a") as f:
      
        for month in range(1,13):
            month_dir = f"{month:02}"
            full_url = url + "/" + month_dir

            response = requests.get(full_url)
            if response.status_code != 200:
                print("Can't get the page")

            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all("a")

            mp3_links = [link["href"] for link in links if "href" in link.attrs and link['href'].endswith(".mp3")]

            for mp3 in mp3_links:
                full_mp3_url = full_url + "/" + mp3
                f.write(full_mp3_url + "\n")

def main():
    parse_arguments();

    if args.c:
        # print("Using Channel stream")
        audio_url = channel_scraper(args.c);
        
        if args.m:
            mpv_player_url(audio_url);
        else:
            vlc_player(audio_url);

    elif args.u:
            
            audio_url = get_audio_url(args.u);

            if args.m:
                mpv_player_url(audio_url);
            else:
                vlc_player(audio_url);

    elif args.w:
        print("Website choosen")

        url = LOFI_GIRL_BASE_URL + str(args.w)

        print(url)

        website_scraper(url)

        if args.m:
            mpv_player_url('./playlist.m3u')
        else:
            print("VLC Player not avaiable")

if __name__ == "__main__":
    main(); 
