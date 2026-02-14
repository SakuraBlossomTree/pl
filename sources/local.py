"""Local music library scanner and indexer."""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.wavpack import WavPack
from mutagen.mp4 import MP4
from concurrent.futures import ThreadPoolExecutor
import time

from config import MUSIC_FOLDER, LIBRARY_INDEX_FILE, SUPPORTED_AUDIO_FORMATS
from player.mpv_backend import Track


@dataclass
class TrackMetadata:
    """Metadata for a music track."""
    path: str
    title: str
    artist: str
    album: str
    duration: float
    year: Optional[str] = None
    genre: Optional[str] = None
    track_number: Optional[int] = None
    modified_time: float = 0.0
    
    def to_track(self) -> Track:
        """Convert to Track object."""
        return Track(
            title=self.title,
            artist=self.artist,
            path=self.path,
            duration=self.duration,
            source="local"
        )


class MusicLibrary:
    """Manages the local music library."""
    
    def __init__(self, music_folder: Path = MUSIC_FOLDER):
        self.music_folder = Path(music_folder)
        self.index: Dict[str, TrackMetadata] = {}
        self.last_scan_time: float = 0
        self._load_index()
    
    def _load_index(self):
        """Load the library index from cache."""
        if LIBRARY_INDEX_FILE.exists():
            try:
                with open(LIBRARY_INDEX_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.index = {
                        path: TrackMetadata(**meta) 
                        for path, meta in data.get('tracks', {}).items()
                    }
                    self.last_scan_time = data.get('last_scan', 0)
            except Exception as e:
                print(f"Error loading library index: {e}")
                self.index = {}
    
    def _save_index(self):
        """Save the library index to cache."""
        try:
            data = {
                'tracks': {
                    path: asdict(meta) 
                    for path, meta in self.index.items()
                },
                'last_scan': self.last_scan_time
            }
            with open(LIBRARY_INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving library index: {e}")
    
    def _extract_metadata(self, file_path: Path) -> Optional[TrackMetadata]:
        """Extract metadata from an audio file."""
        try:
            suffix = file_path.suffix.lower()
            
            if suffix == '.mp3':
                audio = MP3(str(file_path))
            elif suffix == '.flac':
                audio = FLAC(str(file_path))
            elif suffix == '.ogg':
                audio = OggVorbis(str(file_path))
            elif suffix == '.wav':
                audio = WavPack(str(file_path))
            elif suffix in ['.m4a', '.mp4']:
                audio = MP4(str(file_path))
            else:
                return None
            
            # Get tags
            tags = audio.tags
            
            def get_tag(*keys: str) -> str:
                """Try multiple tag keys."""
                for key in keys:
                    if tags and key in tags:
                        val = tags[key]
                        if isinstance(val, list):
                            return str(val[0])
                        return str(val)
                return ""
            
            title = get_tag('TIT2', 'TITLE', '©nam') or file_path.stem
            artist = get_tag('TPE1', 'ARTIST', '©ART') or "Unknown Artist"
            album = get_tag('TALB', 'ALBUM', '©alb') or "Unknown Album"
            year = get_tag('TDRC', 'DATE', '©day') or None
            genre = get_tag('TCON', 'GENRE', '©gen') or None
            
            track_num = None
            track_str = get_tag('TRCK', 'TRACKNUMBER', 'trkn')
            if track_str:
                try:
                    track_num = int(track_str.split('/')[0])
                except ValueError:
                    pass
            
            return TrackMetadata(
                path=str(file_path),
                title=title,
                artist=artist,
                album=album,
                duration=getattr(audio.info, 'length', 0.0),
                year=year,
                genre=genre,
                track_number=track_num,
                modified_time=file_path.stat().st_mtime
            )
            
        except Exception as e:
            # Return basic metadata on error
            return TrackMetadata(
                path=str(file_path),
                title=file_path.stem,
                artist="Unknown Artist",
                album="Unknown Album",
                duration=0.0,
                modified_time=file_path.stat().st_mtime
            )
    
    def scan(self, force: bool = False) -> int:
        """Scan the music folder and update the index.
        
        Returns number of tracks found.
        """
        if not self.music_folder.exists():
            return 0
        
        # Find all audio files
        audio_files = []
        for ext in SUPPORTED_AUDIO_FORMATS:
            audio_files.extend(self.music_folder.rglob(f"*{ext}"))
        
        # Check which files need updating
        files_to_scan = []
        if not force:
            for file_path in audio_files:
                path_str = str(file_path)
                if path_str not in self.index:
                    files_to_scan.append(file_path)
                elif file_path.stat().st_mtime > self.index[path_str].modified_time:
                    files_to_scan.append(file_path)
        else:
            files_to_scan = audio_files
        
        # Scan files in parallel
        if files_to_scan:
            print(f"Scanning {len(files_to_scan)} new/modified files...")
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = executor.map(self._extract_metadata, files_to_scan)
                
            for result in results:
                if result:
                    self.index[result.path] = result
        
        # Remove deleted files from index
        current_paths = {str(p) for p in audio_files}
        self.index = {k: v for k, v in self.index.items() if k in current_paths}
        
        self.last_scan_time = time.time()
        self._save_index()
        
        return len(self.index)
    
    def get_all_tracks(self) -> List[Track]:
        """Get all tracks in the library."""
        return [meta.to_track() for meta in self.index.values()]
    
    def search(self, query: str) -> List[Track]:
        """Simple search by title, artist, or album."""
        query = query.lower()
        results = []
        for meta in self.index.values():
            if (query in meta.title.lower() or 
                query in meta.artist.lower() or 
                query in meta.album.lower()):
                results.append(meta.to_track())
        return results
    
    def get_artists(self) -> List[str]:
        """Get list of all artists."""
        artists = set()
        for meta in self.index.values():
            if meta.artist:
                artists.add(meta.artist)
        return sorted(artists)
    
    def get_albums(self) -> List[str]:
        """Get list of all albums."""
        albums = set()
        for meta in self.index.values():
            if meta.album:
                albums.add(meta.album)
        return sorted(albums)
    
    def get_tracks_by_artist(self, artist: str) -> List[Track]:
        """Get all tracks by a specific artist."""
        return [
            meta.to_track() 
            for meta in self.index.values() 
            if meta.artist.lower() == artist.lower()
        ]
    
    def get_tracks_by_album(self, album: str) -> List[Track]:
        """Get all tracks from a specific album."""
        return [
            meta.to_track() 
            for meta in self.index.values() 
            if meta.album.lower() == album.lower()
        ]
    
    def get_folders(self) -> List[str]:
        """Get list of all folders (subdirectories) in the music library."""
        folders = set()
        for path_str in self.index.keys():
            path = Path(path_str)
            try:
                # Get relative path from music folder
                rel_path = path.relative_to(self.music_folder)
                # Get the first directory component
                if len(rel_path.parts) > 1:
                    folders.add(rel_path.parts[0])
            except ValueError:
                pass
        return sorted(folders)
    
    def get_tracks_in_folder(self, folder: str) -> List[Track]:
        """Get all tracks in a specific folder."""
        tracks = []
        folder_path = self.music_folder / folder
        for path_str, meta in self.index.items():
            if path_str.startswith(str(folder_path)):
                tracks.append(meta.to_track())
        return tracks
