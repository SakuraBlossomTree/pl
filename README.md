# Lofi Music Player

A beautiful Terminal User Interface (TUI) music player built with Python and Rich, featuring YouTube search, local library support, and fuzzy search.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Local Library**: Automatically scans and indexes your `~/Music` folder
- **YouTube Search**: Search and stream lofi music directly from YouTube
- **Fuzzy Search**: Built-in fuzzy finder for quick track discovery
- **Queue Management**: Add, remove, and reorder tracks in the queue
- **Download Support**: Save YouTube tracks to your local library
- **Beautiful TUI**: Rich terminal interface with smooth animations
- **Vim-like Controls**: Intuitive keyboard shortcuts

## Requirements

### System Dependencies
- **mpv** - Media player backend
  - macOS: `brew install mpv`
  - Ubuntu/Debian: `sudo apt install mpv`
  - Windows: Download from [mpv.io](https://mpv.io/installation/)
  - Arch: `sudo pacman -S mpv`

- **FFmpeg** (optional, for YouTube downloads)
  - Required if you want to download YouTube tracks
  - Usually comes with mpv or can be installed separately

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation

1. Clone or download this repository:
```bash
cd lofi-player
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure mpv is installed on your system (see Requirements)

## Usage

Run the player:
```bash
python main.py
```

### Keyboard Shortcuts

#### Navigation
- `1` - Switch to Library tab
- `2` - Switch to YouTube tab
- `/` - Switch to Search tab
- `Tab` - Switch focus
- `↑/↓` - Navigate lists
- `?` - Toggle help

#### Playback
- `Space` - Play/Pause
- `N` or `→` - Next track
- `P` or `←` - Previous track
- `L` or `Shift+→` - Seek forward 10s
- `H` or `Shift+←` - Seek backward 10s
- `+` or `=` - Volume up
- `-` - Volume down

#### Queue Management
- `A` - Add selected track to queue
- `D` - Remove track from queue
- `C` - Clear queue
- `Enter` - Play selected track immediately

#### YouTube
- `Ctrl+D` - Toggle auto-download mode

#### General
- `Q` or `Ctrl+C` - Quit

## How It Works

### Local Library
The player automatically scans your `~/Music` folder on startup, extracting metadata (title, artist, album, duration) from audio files. Supported formats:
- MP3
- FLAC
- OGG
- WAV
- M4A/AAC
- WMA

The library index is cached for faster subsequent startups.

### YouTube Integration
- Search YouTube directly from the TUI
- Stream audio without downloading
- Optionally download tracks to your local library (saved to `~/Music/youtube-downloads/`)

### Fuzzy Search
The built-in fuzzy finder uses rapidfuzz for fast, accurate searching across both your local library and YouTube results.

## Configuration

Edit `config.py` to customize:
- Music folder location (default: `~/Music`)
- Key bindings
- Number of YouTube search results
- Cache locations

## Project Structure

```
lofi-player/
├── main.py                  # Entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── player/
│   ├── mpv_backend.py     # MPV media player wrapper
│   └── queue.py           # Playlist management
├── sources/
│   ├── local.py           # Local music library scanner
│   └── youtube.py         # YouTube search & streaming
├── search/
│   └── fuzzy.py           # Fuzzy search engine
└── tui/
    ├── app.py             # Main TUI application
    ├── components.py      # UI components
    ├── input_handler.py   # Keyboard input handling
    └── styles.py          # Rich theme & styles
```

## Troubleshooting

### "mpv not found" error
Make sure mpv is installed and available in your system PATH.

### "No module named 'mpv'" error
Install python-mpv: `pip install python-mpv`

### YouTube search not working
- Check your internet connection
- Try updating yt-dlp: `pip install -U yt-dlp`
- Some videos may be region-restricted

### Terminal issues on Windows
- Use Windows Terminal for best experience
- ConEmu and Cmder also work well
- Standard CMD may have limited functionality

## License

MIT License - feel free to use, modify, and distribute!

## Credits

- Built with [Rich](https://github.com/Textualize/rich) for the TUI
- Music playback via [python-mpv](https://github.com/jaseg/python-mpv)
- YouTube integration via [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Fuzzy search via [rapidfuzz](https://github.com/maxbachmann/RapidFuzz)

---

Enjoy your lofi beats!
