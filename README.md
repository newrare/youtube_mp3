# YouTube to MP3 Converter

## About the Project

This project is a complete audio management suite that includes:
- **main.py** - Convert YouTube videos or playlists into MP3 files
- **folder.py** - Rename and normalize audio files in directories
- **tag.py** - Update and standardize audio file metadata
- **Tool.py** - Shared utility module with common functions

## Features

### main.py - YouTube to MP3 Converter
Downloads YouTube videos or entire playlists and converts them to MP3 format.
- Automatic YouTube compatibility updates
- Supports both single videos and playlists
- Stores files in organized directory structure
- Automatic name normalization

**Usage:**
```sh
python main.py <youtube_url>
# or
python main.py
# Then enter URL when prompted
```

### folder.py - Audio File Renaming
Intelligently renames audio files in directories with pattern detection.
- Recursively processes subdirectories
- Detects and removes common filename prefixes/patterns
- Automatically detects and removes track numbers (if 70%+ of files have them)
- Applies consistent name normalization

**Usage:**
```sh
python folder.py <directory_path>
# or
python folder.py
# Then enter path when prompted
```

### tag.py - Audio Tag Management
Updates and standardizes audio file metadata (ID3 tags, FLAC, MP4, etc.).
- Auto-creates missing ID3 tags
- Detects common artist/album names across files
- Validates and normalizes genres
- Supports multiple audio formats: MP3, FLAC, M4A, MP4, OGG, WAV

**Usage:**
```sh
python tag.py <directory_path>
# or
python tag.py
# Then enter path when prompted
```

### Tool.py - Shared Utilities
Centralized module containing:
- `convert_name()` - Normalizes filenames/text
- `AUDIO_EXTENSIONS` - List of supported audio file extensions

## Installation

Install all dependencies:

```sh
pip install -r requirements.txt
```

### Requirements
- Python 3.7+
- yt_dlp >= 2024.0.0
- requests >= 2.31.0
- mutagen >= 1.47.0

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
