"""TUI components for the lofi music player."""
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.box import ROUNDED, SIMPLE
from rich.layout import Layout
from rich.console import Group
from rich.align import Align

from player.mpv_backend import Track, MPVPlayer
from tui.styles import (
    LOFI_THEME, PROGRESS_CHAR, PROGRESS_EMPTY_CHAR, PROGRESS_WIDTH,
    STYLE_SELECTED, STYLE_CURRENT, STYLE_YOUTUBE, STYLE_LOCAL
)


class PlayerDisplay:
    """Displays the current player state."""
    
    def __init__(self, player: MPVPlayer):
        self.player = player
        self.show_time_remaining = False
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def _render_progress_bar(self, position: float, duration: float) -> Text:
        """Render a progress bar."""
        if duration <= 0:
            return Text(PROGRESS_EMPTY_CHAR * PROGRESS_WIDTH, style="dim")
        
        progress = min(position / duration, 1.0)
        filled = int(PROGRESS_WIDTH * progress)
        empty = PROGRESS_WIDTH - filled
        
        bar = Text()
        bar.append(PROGRESS_CHAR * filled, style="bright_cyan")
        bar.append(PROGRESS_EMPTY_CHAR * empty, style="dim")
        return bar
    
    def render(self) -> Panel:
        """Render the player display panel."""
        track = self.player.current_track
        
        if not track:
            content = Align.center(
                Text("No track playing", style="dim italic"),
                vertical="middle"
            )
            return Panel(
                content,
                title="[bold]Now Playing[/bold]",
                border_style="border.player",
                box=ROUNDED,
                height=10
            )
        
        # Track info
        title_text = Text(track.title, style="player.title", overflow="ellipsis")
        artist_text = Text(track.artist, style="player.artist")
        
        # Source indicator
        source_indicator = "[YT]" if track.source == "youtube" else "[MUSIC]"
        
        # Time display
        position = self.player.position
        duration = track.duration or self.player.duration
        
        if self.show_time_remaining and duration > 0:
            time_text = Text(f"-{self._format_time(duration - position)}")
        else:
            time_text = Text(self._format_time(position))
        
        time_text.append(" / ", style="dim")
        time_text.append(self._format_time(duration), style="dim")
        
        # Progress bar
        progress = self._render_progress_bar(position, duration)
        
        # Volume
        volume_text = Text(f"VOL {self.player.volume}%", style="player.volume")
        
        # Status
        if self.player.is_playing:
            status = Text("> Playing", style="status.playing")
        else:
            status = Text("|| Paused", style="status.paused")
        
        # Build content
        content = Group(
            Text(f"{source_indicator}", style="yellow"),
            title_text,
            artist_text,
            Text(),
            Group(
                Align.center(progress),
                Align.center(time_text)
            ),
            Text(),
            Group(
                Align.left(status),
                Align.right(volume_text)
            )
        )
        
        return Panel(
            content,
            title=f"[bold]{'YouTube' if track.source == 'youtube' else 'Local'}[/bold]",
            border_style="border.player",
            box=ROUNDED,
            height=12
        )


class QueueDisplay:
    """Displays the playback queue."""
    
    def __init__(self, player: MPVPlayer):
        self.player = player
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_items = 15
    
    def _format_duration(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        if seconds <= 0:
            return "--:--"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def render(self) -> Panel:
        """Render the queue panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("#", width=3, justify="right")
        table.add_column("Title", ratio=3)
        table.add_column("Duration", width=6, justify="right")
        
        if not self.player.queue:
            table.add_row("", Text("Queue is empty", style="dim italic"), "")
        else:
            # Calculate visible range
            total_items = len(self.player.queue)
            half_visible = self.visible_items // 2
            
            if self.selected_index < half_visible:
                start = 0
            elif self.selected_index > total_items - half_visible:
                start = max(0, total_items - self.visible_items)
            else:
                start = self.selected_index - half_visible
            
            end = min(start + self.visible_items, total_items)
            
            for i in range(start, end):
                track = self.player.queue[i]
                is_current = (i == self.player.current_index)
                is_selected = (i == self.selected_index)
                
                # Number
                num = Text(f"{i + 1}", style="queue.number")
                if is_current:
                    num = Text(">", style="bright_green")
                
                # Title and artist
                title_text = Text()
                
                if track.source == "youtube":
                    title_text.append("[YT] ", style="queue.youtube")
                
                title_text.append(track.title, style="queue.title")
                
                if track.artist:
                    title_text.append(f" - {track.artist}", style="queue.artist")
                
                # Apply selection/current styling
                if is_current:
                    title_text.stylize("bold green")
                elif is_selected:
                    title_text.stylize("reverse")
                
                # Duration
                duration = Text(
                    self._format_duration(track.duration),
                    style="dim" if not is_current else "green"
                )
                
                table.add_row(num, title_text, duration)
        
        queue_info = f" {len(self.player.queue)} tracks "
        if self.player.current_index >= 0:
            queue_info = f" {self.player.current_index + 1}/{len(self.player.queue)} "
        
        return Panel(
            table,
            title=f"[bold]Queue[/bold]{queue_info}",
            border_style="border.queue",
            box=ROUNDED
        )
    
    def move_selection(self, delta: int):
        """Move selection up or down."""
        if self.player.queue:
            self.selected_index = max(0, min(len(self.player.queue) - 1, 
                                              self.selected_index + delta))


class SearchDisplay:
    """Search interface."""
    
    def __init__(self):
        self.query = ""
        self.results: List[Track] = []
        self.selected_index = 0
        self.searching = False
        self.search_callback: Optional[Callable[[str], List[Track]]] = None
    
    def set_search_callback(self, callback: Callable[[str], List[Track]]):
        """Set the search callback function."""
        self.search_callback = callback
    
    def update_query(self, char: str):
        """Add character to query."""
        self.query += char
        self._perform_search()
    
    def backspace(self):
        """Remove last character from query."""
        self.query = self.query[:-1]
        self._perform_search()
    
    def clear(self):
        """Clear the search query."""
        self.query = ""
        self.results.clear()
        self.selected_index = 0
    
    def _perform_search(self):
        """Execute search with current query."""
        if self.search_callback and self.query:
            self.results = self.search_callback(self.query)
            self.selected_index = 0
    
    def render(self, title: str = "Search") -> Panel:
        """Render the search panel."""
        # Query display
        query_display = Text()
        query_display.append("> ", style="bright_cyan")
        query_display.append(self.query if self.query else "Type to search...", 
                            style="search.query" if self.query else "dim italic")
        
        if self.searching:
            query_display.append(" [WAIT]", style="yellow")
        
        # Results
        if self.results:
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("#", width=3)
            table.add_column("Result", ratio=1)
            
            for i, track in enumerate(self.results[:20]):
                is_selected = (i == self.selected_index)
                
                num = Text(f"{i + 1}", style="dim")
                
                result_text = Text()
                if track.source == "youtube":
                    result_text.append("[YT] ", style="bright_red")
                
                result_text.append(track.title)
                if track.artist:
                    result_text.append(f" - {track.artist}", style="dim")
                
                if is_selected:
                    result_text.stylize("reverse")
                
                table.add_row(num, result_text)
            
            content = Group(query_display, Text(), table)
        else:
            if self.query:
                content = Group(query_display, Text(), 
                              Text("No results found", style="dim italic"))
            else:
                content = Group(query_display, Text(),
                              Text("Start typing to search", style="dim italic"))
        
        result_count = f" ({len(self.results)} results)" if self.results else ""
        
        return Panel(
            content,
            title=f"[bold]{title}[/bold]{result_count}",
            border_style="border.search",
            box=ROUNDED
        )
    
    def move_selection(self, delta: int):
        """Move selection up or down."""
        if self.results:
            self.selected_index = max(0, min(len(self.results) - 1,
                                              self.selected_index + delta))
    
    def get_selected(self) -> Optional[Track]:
        """Get the currently selected track."""
        if 0 <= self.selected_index < len(self.results):
            return self.results[self.selected_index]
        return None


class LibraryDisplay:
    """Displays the local music library with folder navigation."""
    
    def __init__(self, library):
        self.library = library
        self.folders: List[str] = []
        self.tracks_in_folder: List[Track] = []
        self.selected_index = 0
        self.current_folder: Optional[str] = None
        self.view_mode = "folders"  # "folders" or "tracks"
        self.visible_items = 20
        self._load_folders()
    
    def _load_folders(self):
        """Load all folders from the library."""
        self.folders = self.library.get_folders()
        if not self.folders:
            # If no subfolders, show all tracks at root
            self.view_mode = "tracks"
            self.tracks_in_folder = self.library.get_all_tracks()
    
    def _format_duration(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        if seconds <= 0:
            return "--:--"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def enter_folder(self, folder: str):
        """Enter a folder to view its tracks."""
        self.current_folder = folder
        self.view_mode = "tracks"
        self.tracks_in_folder = self.library.get_tracks_in_folder(folder)
        self.selected_index = 0
    
    def go_back(self):
        """Go back to folder list."""
        self.current_folder = None
        self.view_mode = "folders"
        self.selected_index = 0
    
    def render(self) -> Panel:
        """Render the library panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("#", width=4, justify="right")
        table.add_column("Name", ratio=3)
        table.add_column("Info", width=10, justify="right")
        
        if self.view_mode == "folders":
            # Show folders
            if not self.folders:
                table.add_row("", Text("No folders found", style="dim italic"), "")
            else:
                items = self.folders
                title = "Library - Folders"
        else:
            # Show tracks in current folder
            if not self.tracks_in_folder:
                table.add_row("", Text("No tracks in folder", style="dim italic"), "")
                items = []
                title = f"Library - {self.current_folder}"
            else:
                items = self.tracks_in_folder
                title = f"Library - {self.current_folder}"
        
        if items:
            total = len(items)
            
            # Calculate visible range
            half = self.visible_items // 2
            if self.selected_index < half:
                start = 0
            elif self.selected_index > total - half:
                start = max(0, total - self.visible_items)
            else:
                start = self.selected_index - half
            
            end = min(start + self.visible_items, total)
            
            for i in range(start, end):
                is_selected = (i == self.selected_index)
                
                num = Text(f"{i + 1}", style="dim")
                
                if self.view_mode == "folders":
                    # Show folder
                    folder_name = items[i]
                    name_text = Text()
                    name_text.append("[FOLDER] ", style="bright_blue")
                    name_text.append(folder_name, style="library.folder")
                    
                    # Count tracks in folder
                    track_count = len(self.library.get_tracks_in_folder(folder_name))
                    info_text = Text(f"{track_count} tracks", style="dim")
                else:
                    # Show track
                    track = items[i]
                    name_text = Text()
                    name_text.append(track.title, style="library.track")
                    
                    if track.artist and track.artist != "Unknown Artist":
                        name_text.append(f" - {track.artist}", style="library.artist")
                    
                    info_text = Text(self._format_duration(track.duration), style="dim")
                
                if is_selected:
                    name_text.stylize("reverse")
                
                table.add_row(num, name_text, info_text)
        
        # Add back button hint when in tracks view
        if self.view_mode == "tracks":
            info = f" ({len(self.tracks_in_folder)} tracks) - Press BACKSPACE to go back"
        else:
            info = f" ({len(self.folders)} folders, {len(self.library.get_all_tracks())} total tracks)"
        
        return Panel(
            table,
            title=f"[bold]{title}[/bold]{info}",
            border_style="border.library",
            box=ROUNDED
        )
    
    def move_selection(self, delta: int):
        """Move selection up or down."""
        items = self.folders if self.view_mode == "folders" else self.tracks_in_folder
        if items:
            self.selected_index = max(0, min(len(items) - 1,
                                              self.selected_index + delta))
    
    def get_selected(self):
        """Get the currently selected item (folder or track)."""
        if self.view_mode == "folders":
            if 0 <= self.selected_index < len(self.folders):
                return self.folders[self.selected_index]
        else:
            if 0 <= self.selected_index < len(self.tracks_in_folder):
                return self.tracks_in_folder[self.selected_index]
        return None
    
    def update_library(self, library):
        """Update the library reference."""
        self.library = library
        self._load_folders()
        self.selected_index = 0
        self.current_folder = None
        self.view_mode = "folders"
