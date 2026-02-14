"""Playlist queue management."""
from typing import List, Optional
from dataclasses import dataclass, field
from .mpv_backend import Track


@dataclass
class Playlist:
    """Manages a playlist queue."""
    name: str
    tracks: List[Track] = field(default_factory=list)
    current_index: int = -1
    shuffle: bool = False
    repeat: bool = False
    
    @property
    def current_track(self) -> Optional[Track]:
        """Get the current track."""
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    @property
    def is_empty(self) -> bool:
        """Check if playlist is empty."""
        return len(self.tracks) == 0
    
    def add(self, track: Track):
        """Add a track to the playlist."""
        self.tracks.append(track)
    
    def add_many(self, tracks: List[Track]):
        """Add multiple tracks."""
        self.tracks.extend(tracks)
    
    def remove(self, index: int) -> Optional[Track]:
        """Remove a track at index."""
        if 0 <= index < len(self.tracks):
            if index == self.current_index:
                self.current_index = -1
            elif index < self.current_index:
                self.current_index -= 1
            return self.tracks.pop(index)
        return None
    
    def clear(self):
        """Clear all tracks."""
        self.tracks.clear()
        self.current_index = -1
    
    def move(self, from_index: int, to_index: int):
        """Move a track from one position to another."""
        if 0 <= from_index < len(self.tracks) and 0 <= to_index < len(self.tracks):
            track = self.tracks.pop(from_index)
            self.tracks.insert(to_index, track)
            
            if from_index == self.current_index:
                self.current_index = to_index
            elif from_index < self.current_index <= to_index:
                self.current_index -= 1
            elif to_index <= self.current_index < from_index:
                self.current_index += 1
    
    def next(self) -> Optional[Track]:
        """Get next track."""
        if self.current_index + 1 < len(self.tracks):
            self.current_index += 1
            return self.current_track
        elif self.repeat and len(self.tracks) > 0:
            self.current_index = 0
            return self.current_track
        return None
    
    def prev(self) -> Optional[Track]:
        """Get previous track."""
        if self.current_index > 0:
            self.current_index -= 1
            return self.current_track
        elif self.repeat and len(self.tracks) > 0:
            self.current_index = len(self.tracks) - 1
            return self.current_track
        return None
    
    def set_index(self, index: int) -> Optional[Track]:
        """Set current track by index."""
        if 0 <= index < len(self.tracks):
            self.current_index = index
            return self.current_track
        return None
    
    def __len__(self) -> int:
        return len(self.tracks)
    
    def __getitem__(self, index: int) -> Track:
        return self.tracks[index]
    
    def __iter__(self):
        return iter(self.tracks)
