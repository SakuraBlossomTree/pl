"""Configuration settings for the lofi music player."""
import os
from pathlib import Path

MUSIC_FOLDER = Path.home() / "Music"
CACHE_FOLDER = Path.home() / ".cache" / "lofi-player"
DOWNLOADS_FOLDER = MUSIC_FOLDER / "youtube-downloads"

CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
DOWNLOADS_FOLDER.mkdir(parents=True, exist_ok=True)

LIBRARY_INDEX_FILE = CACHE_FOLDER / "library_index.json"
YOUTUBE_CACHE_FILE = CACHE_FOLDER / "youtube_cache.json"

SUPPORTED_AUDIO_FORMATS = {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma'}

YOUTUBE_SEARCH_RESULTS = 10

KEY_BINDINGS = {
    'quit': ['q', 'ctrl+c'],
    'play_pause': ['space'],
    'next': ['n', 'right'],
    'prev': ['p', 'left'],
    'volume_up': ['+', '='],
    'volume_down': ['-'],
    'seek_forward': ['l', 'shift+right'],
    'seek_backward': ['h', 'shift+left'],
    'search': ['/'],
    'queue': ['tab'],
    'library': ['1'],
    'youtube': ['2'],
    'add_to_queue': ['a'],
    'remove_from_queue': ['d'],
    'clear_queue': ['c'],
    'toggle_download': ['ctrl+d'],
    'help': ['?'],
}
