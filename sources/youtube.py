"""YouTube search and streaming using yt-dlp."""
import json
import asyncio
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import yt_dlp
import aiohttp

from config import YOUTUBE_CACHE_FILE, YOUTUBE_SEARCH_RESULTS, DOWNLOADS_FOLDER
from player.mpv_backend import Track


@dataclass
class YouTubeVideo:
    """Represents a YouTube video."""
    video_id: str
    title: str
    artist: str
    duration: float
    thumbnail: str
    view_count: int
    url: str
    
    def to_track(self) -> Track:
        """Convert to Track object for playback."""
        return Track(
            title=self.title,
            artist=self.artist,
            path=self.url,
            duration=self.duration,
            source="youtube",
            youtube_id=self.video_id,
            thumbnail=self.thumbnail
        )


class YouTubeSource:
    """Handles YouTube search and streaming."""
    
    def __init__(self):
        self.cache: dict = {}
        self._load_cache()
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    
    def _load_cache(self):
        """Load search cache."""
        if YOUTUBE_CACHE_FILE.exists():
            try:
                with open(YOUTUBE_CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}
    
    def _save_cache(self):
        """Save search cache."""
        try:
            with open(YOUTUBE_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def search(self, query: str, max_results: int = YOUTUBE_SEARCH_RESULTS) -> List[YouTubeVideo]:
        """Search YouTube for videos."""
        cache_key = f"search:{query.lower()}"
        
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return [YouTubeVideo(**v) for v in cached]
        
        try:
            search_query = f"ytsearch{max_results}:{query}"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                result = ydl.extract_info(search_query, download=False)
                
                if not result or 'entries' not in result:
                    return []
                
                videos = []
                for entry in result['entries']:
                    if not entry:
                        continue
                    
                    video_id = entry.get('id', '')
                    title = entry.get('title', 'Unknown Title')
                    channel = entry.get('uploader', 'Unknown Artist')
                    duration = entry.get('duration', 0) or 0
                    thumbnail = entry.get('thumbnail', '')
                    view_count = entry.get('view_count', 0) or 0
                    
                    # Get best audio URL
                    url = entry.get('url', '')
                    if not url and 'formats' in entry:
                        # Find best audio format
                        formats = entry['formats']
                        audio_formats = [f for f in formats if f.get('vcodec') == 'none']
                        if audio_formats:
                            best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
                            url = best_audio.get('url', '')
                    
                    video = YouTubeVideo(
                        video_id=video_id,
                        title=title,
                        artist=channel,
                        duration=duration,
                        thumbnail=thumbnail,
                        view_count=view_count,
                        url=url or f"https://www.youtube.com/watch?v={video_id}"
                    )
                    videos.append(video)
                
                # Cache results
                self.cache[cache_key] = [v.__dict__ for v in videos]
                self._save_cache()
                
                return videos
                
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
    def get_audio_url(self, video_id: str) -> Optional[str]:
        """Get direct audio stream URL for a video."""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'url' in info:
                    return info['url']
                
                # Find best audio format
                if 'formats' in info:
                    formats = info['formats']
                    audio_formats = [f for f in formats if f.get('vcodec') == 'none']
                    if audio_formats:
                        best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
                        return best_audio.get('url')
                
                return None
                
        except Exception as e:
            print(f"Error getting audio URL: {e}")
            return None
    
    def download(self, video: YouTubeVideo, progress_callback=None) -> Optional[Path]:
        """Download a YouTube video as audio."""
        try:
            output_path = DOWNLOADS_FOLDER / f"{video.video_id}.%(ext)s"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_path),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            if progress_callback:
                def hook(d):
                    if d['status'] == 'downloading':
                        progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
                        progress_callback(progress)
                
                ydl_opts['progress_hooks'] = [hook]
            
            url = f"https://www.youtube.com/watch?v={video.video_id}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            downloaded_file = DOWNLOADS_FOLDER / f"{video.video_id}.mp3"
            if downloaded_file.exists():
                return downloaded_file
            
            return None
            
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def get_video_info(self, url: str) -> Optional[YouTubeVideo]:
        """Get info for a single video URL."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                return YouTubeVideo(
                    video_id=info.get('id', ''),
                    title=info.get('title', 'Unknown Title'),
                    artist=info.get('uploader', 'Unknown Artist'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail', ''),
                    view_count=info.get('view_count', 0) or 0,
                    url=info.get('url', url)
                )
                
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None


async def search_youtube_async(query: str, max_results: int = 10) -> List[YouTubeVideo]:
    """Async wrapper for YouTube search."""
    loop = asyncio.get_event_loop()
    yt = YouTubeSource()
    return await loop.run_in_executor(None, yt.search, query, max_results)
