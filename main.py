#!/usr/bin/env python3

# Classes importing
from yt_dlp import YoutubeDL
import vlc
import argparse
import sys
import subprocess
import json

# Test URL
# LOFI_STREAM_URL = "https://www.youtube.com/watch?v=lTRiuFIWV54"

# LOFI_STREAM_URL = "https://www.youtube.com/watch?v=J2i0cZWCdq4"


#Test info_dict




# yt-dlp options
ydl_opts = {

            'format':"mp3/bestaudio/best",
            'quiet': True,
            'noplaylist' : True,
            'extract_flat': True,

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

    streams = []

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(channel_url, download=False)

        entries = info_dict["entries"][1]["entries"]

        for i in range(0,10):
            url = entries[i]["url"]
            title = entries[i]["title"]

            if title and url:
                streams.append({"title" : title, "url" : url})

    # with open('content.txt','w') as f:
    #     json.dump(url,f)

    # for _ in info_dict:
    #     if count >= 10:
    #         break
    #
    #     title = info_dict["title"]
    #
    #     if title:
    #         streams.append({"title:" : title})
    #         count+=1

    # print(streams)

    # print(streams[2]['url'])

    audio_url = streams[2]['url'] 

    converted_url = get_audio_url(audio_url);

    return converted_url

# Function to run the audio stream via the vlc player
def vlc_player(audio_url):

    player = vlc.MediaPlayer(audio_url)
    player.play()

    while True:
        pass

def mpv_player(audio_url):

    subprocess.run(["mpv", audio_url])

def main():
    parse_arguments();
    
    if args.c:
        # print("Using Channel stream")
        audio_url = channel_scraper(args.c);
        
        print(audio_url)

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
if __name__ == "__main__":
    main(); 
