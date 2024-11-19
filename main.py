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

# Lofi Girl Website
LOFI_GIRL_BASE_URL = "https://lofigirl.com/wp-content/uploads/"

# Initialize fzf
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
            description="Which stands for Play Lofi, Is a simple lofi player that scrapes Youtube and Lofi Girl's Website for Music",
            add_help=True,
            )
    parser.add_argument('-u', type=str,help='Specify the Youtube URL for the stream')
    parser.add_argument('-m',action='store_true', help="To use mpv instead of vlc")
    parser.add_argument('-q', action='store_true', help="Runs it in quiet mode")
    parser.add_argument('-c', type=str,help='Specify the Youtube Channel URL for listing of streams')
    parser.add_argument('-w', type=int, help="Scrape from Lofi Girl Website")
    parser.add_argument('-s', action='store_true', help="Add this to play music on shuffle")

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

# Channel Scraper Function
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

# Process for playing mpv player
def mpv_player(audio_url):

    subprocess.run(["mpv", audio_url])

# Function that scrapers Lofi Girl Website based on the year it lists all the files in a playlist.m3u file
def website_scraper(url):

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

# Main function
def main():
    parse_arguments();

    if args.c:
        audio_url = channel_scraper(args.c);
        
        if args.m:
            mpv_player(audio_url);
        else:
            vlc_player(audio_url);

    elif args.u:
            
            audio_url = get_audio_url(args.u);

            if args.m:
                mpv_player(audio_url);
            else:
                vlc_player(audio_url);

    elif args.w:
        print("Website choosen")

        url = LOFI_GIRL_BASE_URL + str(args.w)

        print(url)

        website_scraper(url)

        if args.s:
            if args.m:
                subprocess.run(["mpv", "--shuffle", "./playlist.m3u"])
            else:
                print("VLC player not avaiable")
        elif args.m:
            mpv_player('./playlist.m3u')

        else:
            print("VLC Player not avaiable")

        os.remove("./playlist.m3u")

if __name__ == "__main__":
    main(); 
