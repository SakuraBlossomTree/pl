"""Rich styles and themes for the TUI."""
from rich.style import Style
from rich.theme import Theme

# Custom theme
LOFI_THEME = Theme({
    # General
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "muted": "dim",
    
    # Player
    "player.title": "bold cyan",
    "player.artist": "italic",
    "player.time": "dim",
    "player.progress": "bright_cyan",
    "player.volume": "bright_green",
    
    # Queue
    "queue.current": "bold green on black",
    "queue.number": "dim",
    "queue.title": "white",
    "queue.artist": "dim",
    "queue.youtube": "bright_red",
    
    # Search
    "search.highlight": "bold yellow on black",
    "search.match": "yellow",
    "search.query": "bold cyan",
    
    # Library
    "library.artist": "bright_blue",
    "library.album": "bright_magenta",
    "library.track": "white",
    "library.folder": "blue",
    
    # Borders
    "border": "dim cyan",
    "border.focused": "bright_cyan",
    "border.player": "bright_green",
    "border.queue": "bright_yellow",
    "border.search": "bright_magenta",
    "border.library": "bright_blue",
    
    # Status
    "status.playing": "green",
    "status.paused": "yellow",
    "status.stopped": "red",
    
    # Help
    "help.key": "bold cyan",
    "help.desc": "dim",
})

# Layout styles
PANEL_BORDER_STYLE = "border"
FOCUSED_BORDER_STYLE = "border.focused"

# Progress bar characters
PROGRESS_CHAR = "█"
PROGRESS_EMPTY_CHAR = "░"
PROGRESS_WIDTH = 30

# Common styles
STYLE_SELECTED = Style(color="black", bgcolor="bright_cyan", bold=True)
STYLE_CURRENT = Style(color="bright_green", bold=True)
STYLE_YOUTUBE = Style(color="bright_red")
STYLE_LOCAL = Style(color="bright_blue")
