"""Main TUI application using Rich."""

import sys
import asyncio
import threading
from typing import Optional, List
from threading import Thread
import time

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED

from player.mpv_backend import MPVPlayer, Track
from sources.local import MusicLibrary
from sources.youtube import YouTubeSource
from search.fuzzy import FuzzySearcher
from tui.components import PlayerDisplay, SearchDisplay, LibraryDisplay
from tui.styles import LOFI_THEME
from tui.input_handler import KeyboardHandler


class LofiPlayerApp:
    """Main lofi music player application."""

    def __init__(self):
        self.console = Console(theme=LOFI_THEME)
        self.player = MPVPlayer()
        self.library = MusicLibrary()
        self.youtube = YouTubeSource()
        self.fuzzy_searcher = FuzzySearcher()

        # UI Components
        self.player_display = PlayerDisplay(self.player)
        self.search_display = SearchDisplay()
        self.library_display: Optional[LibraryDisplay] = None

        # State
        self.active_tab = "library"  # "library", "search", "youtube"
        self.show_help = False
        self.running = True
        self.needs_refresh = True

        # Set up callbacks
        self.player.register_callback("track_start", self._on_track_start)
        self.player.register_callback("track_end", self._on_track_end)

        # Set up search callbacks
        self.search_display.set_search_callback(self._search_callback)

        # Keyboard handler
        self.keyboard_handler: Optional[KeyboardHandler] = None

    def _on_track_start(self, track: Track):
        """Handle track start event."""
        self.needs_refresh = True

    def _on_track_end(self, track: Track):
        """Handle track end event."""
        self.needs_refresh = True

    def _search_callback(self, query: str) -> List[Track]:
        """Perform fuzzy search on library."""
        if self.library_display:
            return self.fuzzy_searcher.search_fast(query, limit=20)
        return []

    def initialize(self):
        """Initialize the application."""
        self.console.print("[bold cyan][MUSIC] Lofi Music Player[/bold cyan]")
        self.console.print("[dim]Scanning library...[/dim]")

        # Scan library
        track_count = self.library.scan()
        self.console.print(f"[green][OK] Found {track_count} tracks[/green]")

        # Show controls hint
        self.console.print(
            "\n[dim]Controls: 1=Library 2=YouTube /=Search ?=Help q=Quit[/dim]"
        )
        self.console.print(
            "[dim]Library: Enter=Open folder/Play Backspace=Go back[/dim]\n"
        )

        # Initialize library display with folder navigation
        self.library_display = LibraryDisplay(self.library)
        self.fuzzy_searcher.index(self.library.get_all_tracks())

        # Small delay for user to see the init message
        time.sleep(1.0)

    def create_layout(self) -> Layout:
        """Create the main layout."""
        layout = Layout()

        # Split into sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        # Header
        header_text = Text()
        header_text.append("[MUSIC] ", style="bold")
        header_text.append("Lofi Player", style="bold cyan")

        # Tab indicators
        tabs = [
            ("1:Library", self.active_tab == "library"),
            ("2:YouTube", self.active_tab == "youtube"),
            ("/:Search", self.active_tab == "search"),
        ]

        tab_text = Text()
        for i, (name, active) in enumerate(tabs):
            if i > 0:
                tab_text.append(" | ", style="dim")
            style = "bold cyan" if active else "dim"
            tab_text.append(name, style=style)

        header_content = Text.assemble(header_text, Text("  "), tab_text)

        layout["header"].update(
            Panel(Align.center(header_content), box=ROUNDED, border_style="dim cyan")
        )

        # Main content area
        if self.show_help:
            layout["main"].update(self._create_help_panel())
        else:
            layout["main"].split_row(
                Layout(name="left", ratio=2), Layout(name="right", ratio=3)
            )

            # Left side: Player only
            layout["left"].update(self.player_display.render())

            # Right side: Active tab
            if self.active_tab == "library" and self.library_display:
                layout["right"].update(self.library_display.render())
            elif self.active_tab == "search":
                layout["right"].update(self.search_display.render("Library Search"))
            elif self.active_tab == "youtube":
                layout["right"].update(self.search_display.render("YouTube Search"))

        # Footer: Status and controls
        footer_text = self._create_footer()
        layout["footer"].update(
            Panel(footer_text, box=ROUNDED, border_style="dim cyan")
        )

        return layout

    def _create_footer(self) -> Text:
        """Create the footer text with key bindings."""
        footer = Text()

        controls = [
            ("Space", "Play/Pause"),
            ("N/→", "Next"),
            ("P/←", "Prev"),
            ("+/-", "Volume"),
            ("R", "Loop Mode"),
            ("Enter", "Play"),
            ("A", "Add to Queue"),
            ("Q", "Quit"),
            ("?", "Help"),
        ]

        for i, (key, desc) in enumerate(controls):
            if i > 0:
                footer.append("  ")
            footer.append(f"[{key}]", style="bold cyan")
            footer.append(f" {desc}", style="dim")

        return footer

    def _create_help_panel(self) -> Panel:
        """Create the help panel."""
        help_text = """
[bold cyan]Keyboard Shortcuts[/bold cyan]

[bold]Navigation:[/bold]
  1          - Switch to Library tab
  2          - Switch to YouTube tab
  /          - Switch to Search tab
  Tab        - Switch focus
  ↑/↓        - Navigate list
  ?          - Toggle this help

[bold]Library - Folder Navigation:[/bold]
  Enter      - Open folder or play track
  Backspace  - Go back to folder list
  ESC        - Alternative to Backspace
  Your Music folder subdirectories are shown as folders

[bold]Playback:[/bold]
  Space      - Play/Pause
  N or →     - Next track
  P or ←     - Previous track
  R          - Cycle loop mode (Off/Single/Queue)
  L or Shift+→  - Seek forward 10s
  H or Shift+←  - Seek backward 10s
  + or =     - Volume up
  -          - Volume down
  Enter      - Play selected track

[bold]General:[/bold]
  Q or Ctrl+C  - Quit
        """

        return Panel(
            Align.left(Text.from_markup(help_text)),
            title="[bold]Help[/bold]",
            border_style="bright_cyan",
            box=ROUNDED,
        )

    def handle_input(self, key: str):
        """Handle keyboard input."""
        import logging

        logging.debug(f"handle_input called with key: {key}")
        self.needs_refresh = True

        # 1. Handle critical global keys
        if key == "ctrl+c":
            self.running = False
            return

        # 2. Handle Text Input (Search/YouTube)
        if self.active_tab in ["search", "youtube"]:
            # Capture text input: printable characters and space
            # Exclude control keys that we want to allow for navigation
            is_control_key = key in ["up", "down", "enter", "backspace", "esc", "tab", "ctrl+c"]
            
            if not is_control_key:
                text = None
                if key == "space":
                    text = " "
                elif len(key) == 1 and key.isprintable():
                    text = key
                
                if text:
                    self.search_display.update_query(text)
                    
                    # Trigger appropriate search
                    if self.active_tab == "search":
                        # Library search - use fuzzy search callback
                        self.search_display.trigger_search()
                    elif self.active_tab == "youtube" and len(self.search_display.query) >= 2:
                        # YouTube search - run in thread
                        threading.Thread(
                            target=self._perform_youtube_search,
                            args=(self.search_display.query,),
                        ).start()
                    return

        # 3. Tab Cycling
        if key == "tab":
            modes = ["library", "youtube", "search"]
            if self.active_tab in modes:
                idx = modes.index(self.active_tab)
                self.active_tab = modes[(idx + 1) % len(modes)]
            else:
                self.active_tab = "library"
            return

        # 4. Standard Shortcuts
        # Help toggle
        if key == "?":
            self.show_help = not self.show_help
            return

        if self.show_help:
            self.show_help = False
            return

        # Tab switching (Direct keys)
        if key == "1":
            self.active_tab = "library"
            return
        elif key == "2":
            self.active_tab = "youtube"
            return
        elif key == "/":
            self.active_tab = "search"
            return

        # Playback controls
        if key == "space":
            self.player.toggle_pause()
        elif key in ["n", "right"]:
            self.player.next()
        elif key in ["p", "left"]:
            self.player.prev()
        elif key in ["+", "="]:
            self.player.volume_up()
        elif key == "-":
            self.player.volume_down()
        elif key in ["l", "shift+right"]:
            self.player.seek_relative(10)
        elif key == "r":
            self.player.cycle_loop_mode()

        # Navigation
        elif key == "up":
            self._move_selection(-1)
        elif key == "down":
            self._move_selection(1)
        elif key == "enter":
            logging.debug(f"Enter key pressed in tab: {self.active_tab}")
            if self.active_tab == "library" and self.library_display:
                selected = self.library_display.get_selected()
                if isinstance(selected, str):
                    # It's a folder, enter it
                    self.library_display.enter_folder(selected)
                else:
                    # It's a track, play it
                    self._play_selected()
            else:
                logging.debug(f"Calling _play_selected() for tab: {self.active_tab}")
                self._play_selected()
        elif key in ["backspace", "esc"]:
            # Handle going back from folder in library
            if self.active_tab == "library" and self.library_display:
                if self.library_display.view_mode == "tracks":
                    self.library_display.go_back()
                else:
                    # In folder view, nothing to do
                    pass
            elif self.active_tab in ["search", "youtube"]:
                self.search_display.backspace()
                # Trigger search for library search tab
                if self.active_tab == "search":
                    self.search_display.trigger_search()

        elif key == "a":
            self._add_to_queue()

        # Quit
        elif key == "q":
            self.running = False

    def _add_to_queue(self):
        """Add the selected track to the queue."""
        track = None

        if self.active_tab == "library" and self.library_display:
            selected = self.library_display.get_selected()
            # Only add if it's a track (not a folder)
            if isinstance(selected, Track):
                track = selected
        elif self.active_tab in ["search", "youtube"]:
            track = self.search_display.get_selected()

        if track:
            self.player.add_to_queue(track)

    def _move_selection(self, delta: int):
        """Move selection in the active tab."""
        if self.active_tab == "library" and self.library_display:
            self.library_display.move_selection(delta)
        elif self.active_tab in ["search", "youtube"]:
            self.search_display.move_selection(delta)

    def _play_selected(self):
        """Play the selected track immediately."""
        import logging
        track = None

        if self.active_tab == "library" and self.library_display:
            selected = self.library_display.get_selected()
            # Only play if it's a track (not a folder)
            if isinstance(selected, Track):
                track = selected
        elif self.active_tab in ["search", "youtube"]:
            track = self.search_display.get_selected()
            logging.debug(f"YouTube/Search tab - got track: {track}")
            if track:
                logging.debug(f"  Track title: {track.title}, source: {track.source}")

        if track:
            logging.debug(f"Playing track: {track.title}")
            self.player.play_track(track, add_to_queue=False)
        else:
            logging.debug("No track to play!")

    async def _youtube_search(self):
        """Perform YouTube search."""
        query = self.search_display.query
        if len(query) < 2:
            return

        self.search_display.searching = True
        self.needs_refresh = True

        try:
            # Run search in thread pool
            loop = asyncio.get_event_loop()
            videos = await loop.run_in_executor(None, self.youtube.search, query, 10)

            self.search_display.results = [v.to_track() for v in videos]
            self.search_display.selected_index = 0
        finally:
            self.search_display.searching = False
            self.needs_refresh = True

    def _perform_youtube_search(self, query: str):
        """Perform YouTube search synchronously."""
        if len(query) < 2:
            return

        self.search_display.searching = True
        self.needs_refresh = True

        try:
            videos = self.youtube.search(query, 10)
            self.search_display.results = [v.to_track() for v in videos]
            self.search_display.selected_index = 0
        finally:
            self.search_display.searching = False
            self.needs_refresh = True

    def run(self):
        """Run the main application loop."""
        self.initialize()

        # Start keyboard handler
        self.keyboard_handler = KeyboardHandler(self.handle_input)
        self.keyboard_handler.start()

        try:
            with Live(
                self.create_layout(),
                console=self.console,
                refresh_per_second=10,
                screen=True,
                auto_refresh=True,
            ) as live:
                last_size = None
                while self.running:
                    # Check for terminal resize
                    current_size = self.console.size
                    if current_size != last_size:
                        last_size = current_size
                        self.needs_refresh = True

                    # Update display
                    if self.needs_refresh:
                        live.update(self.create_layout())
                        self.needs_refresh = False

                    # Small sleep to prevent CPU spinning
                    time.sleep(0.05)
        finally:
            # Stop keyboard handler
            if self.keyboard_handler:
                self.keyboard_handler.stop()
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.player.terminate()
        self.console.print("[green]Goodbye![/green]")


def main():
    """Entry point."""
    app = LofiPlayerApp()

    try:
        app.run()
    except KeyboardInterrupt:
        app.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        app.cleanup()
        raise


if __name__ == "__main__":
    main()
