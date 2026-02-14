from typing import Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path

# Note: mpv DLL path must be set in main.py BEFORE importing this module
import mpv


class LoopMode:
    """Loop mode constants."""

    OFF = "off"  # No looping
    SINGLE = "single"  # Loop current track


@dataclass
class Track:
    """Represents a music track."""

    title: str
    artist: str
    path: str
    duration: float = 0.0
    source: str = "local"  # "local" or "youtube"
    youtube_id: Optional[str] = None
    thumbnail: Optional[str] = None

    def __str__(self):
        if self.artist:
            return f"{self.artist} - {self.title}"
        return self.title

    @property
    def is_local(self) -> bool:
        return self.source == "local"

    @property
    def display_name(self) -> str:
        if self.source == "youtube":
            return f"[YT] {self.title}"
        return str(self)


class MPVPlayer:
    """Wrapper around mpv player with queue management."""

    def __init__(self):
        self.player = mpv.MPV(
            ytdl=True,
            input_default_bindings=True,
            input_vo_keyboard=True,
        )
        self.queue: list[Track] = []
        self.current_index: int = -1
        self._current_track: Optional[Track] = None
        self.loop_mode = LoopMode.OFF  # Default to no looping
        self._callbacks: dict[str, list[Callable]] = {
            "track_start": [],
            "track_end": [],
            "progress": [],
        }

        # Set up mpv event handlers
        self.player.observe_property("time-pos", self._on_time_pos)
        self.player.observe_property("duration", self._on_duration)

        @self.player.event_callback("end-file")
        def on_end_file(event):
            self._on_track_end()

    def register_callback(self, event: str, callback: Callable):
        """Register a callback for player events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _trigger(self, event: str, *args):
        """Trigger all callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                print(f"Callback error: {e}")

    def _on_time_pos(self, name: str, value: Any):
        """Handle time position updates."""
        if value is not None:
            self._trigger("progress", value)

    def _on_duration(self, name: str, value: Any):
        """Handle duration updates."""
        if value is not None and self.current_track:
            self.current_track.duration = value

    def _on_track_end(self):
        """Handle track ending."""
        self._trigger("track_end", self.current_track)

        if self.loop_mode == LoopMode.SINGLE:
            # Loop the current track
            if self.current_track:
                self.play_track(self.current_track, add_to_queue=False)
        else:
            # OFF mode: go to next track or stop if at end
            if self.current_index + 1 < len(self.queue):
                self.play_index(self.current_index + 1)
            else:
                self.stop()

    @property
    def current_track(self) -> Optional[Track]:
        """Get the currently playing track."""
        # First check if we have a directly playing track (no queue)
        if self._current_track is not None:
            return self._current_track
        # Otherwise check the queue
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    @property
    def is_playing(self) -> bool:
        """Check if player is currently playing."""
        return self.player.pause is False

    def play_track(self, track: Track, add_to_queue: bool = True):
        """Play a specific track."""
        import logging

        try:
            import os

            logging.info(
                f"Attempting to play track: {track.title} at path: {track.path}"
            )
            if not os.path.exists(track.path):
                logging.error(f"Track file not found: {track.path}")
                print(f"[ERROR] Track file not found: {track.path}")
                return

            # Add to queue if requested
            if add_to_queue:
                self.queue.append(track)
                self.current_index = len(self.queue) - 1

            self._current_track = track
            self.player.play(track.path)
            self._trigger("track_start", track)
            logging.info(f"Successfully started playing: {track.title}")
        except Exception as e:
            logging.exception(f"Failed to play track: {e}")
            print(f"[ERROR] Failed to play track: {e}")

    def play(self):
        """Resume playback."""
        self.player.pause = False

    def pause(self):
        """Pause playback."""
        self.player.pause = True

    def toggle_pause(self):
        """Toggle play/pause."""
        self.player.pause = not self.player.pause

    def stop(self):
        """Stop playback."""
        self.player.stop()
        self._current_track = None
        self.current_index = -1

    def seek(self, seconds: float):
        """Seek to a position in seconds."""
        try:
            self.player.seek(seconds, reference="absolute", precision="exact")
        except Exception:
            try:
                self.player.seek(seconds)
            except Exception:
                pass

    def seek_relative(self, seconds: float):
        """Seek relative to current position."""
        try:
            # Use mpv's relative seek (negative = backward)
            self.player.seek(seconds, reference="relative")
        except Exception:
            pass

    @property
    def volume(self) -> int:
        """Get current volume (0-100)."""
        return int(self.player.volume or 50)

    @volume.setter
    def volume(self, value: int):
        """Set volume (0-100)."""
        self.player.volume = max(0, min(100, value))

    def volume_up(self, delta: int = 5):
        """Increase volume."""
        self.volume = self.volume + delta

    def volume_down(self, delta: int = 5):
        """Decrease volume."""
        self.volume = self.volume - delta

    @property
    def position(self) -> float:
        """Get current playback position in seconds."""
        return float(self.player.time_pos or 0)

    @property
    def duration(self) -> float:
        """Get total duration of current track."""
        return float(self.player.duration or 0)

    def add_to_queue(self, track: Track):
        """Add a track to the queue."""
        self.queue.append(track)
        # If nothing is playing, start playing
        if self.current_index == -1 and len(self.queue) == 1:
            self.play_index(0)

    def remove_from_queue(self, index: int):
        """Remove a track from the queue."""
        if 0 <= index < len(self.queue):
            if index == self.current_index:
                self.stop()
            elif index < self.current_index:
                self.current_index -= 1
            self.queue.pop(index)

    def clear_queue(self):
        """Clear the entire queue."""
        self.stop()
        self.queue.clear()
        self.current_index = -1

    def play_index(self, index: int):
        """Play track at specific index."""
        if 0 <= index < len(self.queue):
            self.current_index = index
            self.play_track(self.queue[index], add_to_queue=False)

    def next(self):
        """Play next track in queue."""
        if self.current_index + 1 < len(self.queue):
            self.play_index(self.current_index + 1)

    def prev(self):
        """Play previous track in queue."""
        if len(self.queue) > 0:
            if self.current_index > 0:
                # Go to previous track in queue
                self.play_index(self.current_index - 1)
            else:
                # Restart current track from beginning
                try:
                    self.player.seek(0, reference="absolute")
                except Exception:
                    try:
                        self.player.seek(0)
                    except Exception:
                        pass

    def move_in_queue(self, from_index: int, to_index: int):
        """Move a track within the queue."""
        if 0 <= from_index < len(self.queue) and 0 <= to_index < len(self.queue):
            track = self.queue.pop(from_index)
            self.queue.insert(to_index, track)

            # Update current_index if needed
            if from_index == self.current_index:
                self.current_index = to_index
            elif from_index < self.current_index <= to_index:
                self.current_index -= 1
            elif to_index <= self.current_index < from_index:
                self.current_index += 1

    def cycle_loop_mode(self):
        """Cycle through loop modes: OFF -> SINGLE -> OFF."""
        modes = [LoopMode.OFF, LoopMode.SINGLE]
        current = modes.index(self.loop_mode)
        self.loop_mode = modes[(current + 1) % len(modes)]

    def set_loop_mode(self, mode: str):
        """Set loop mode directly."""
        if mode in [LoopMode.OFF, LoopMode.SINGLE]:
            self.loop_mode = mode

    def terminate(self):
        """Clean up resources."""
        self.stop()
        self.player.terminate()
