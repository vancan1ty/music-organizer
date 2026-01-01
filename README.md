# Music Organizer Tool

A Python tool that automatically organizes your music collection into a clean, systematic folder structure based on Artist/Album/Track metadata. Supports automatic metadata recognition for untagged files using AcoustID and MusicBrainz.

## Features

- **Automatic Organization**: Organizes music files into `Artist/Album/Track` structure
- **Multiple Audio Formats**: Supports MP3, FLAC, M4A, OGG, Opus, WMA, WAV, and AAC
- **Metadata Reading**: Extracts metadata from audio file tags
- **Audio Fingerprinting**: Identifies untagged files using AcoustID and MusicBrainz
- **Album Art Management**: Automatically copies album art (JPG/PNG) to organized folders as `cover.jpg`
- **In-Place Reorganization**: Move files instead of copying with `--move` flag
- **Dry Run Mode**: Preview changes before applying them
- **Safe Operation**: Copies files (preserves originals) to the destination (unless using `--move`)
- **Comprehensive Logging**: Logs all operations to `music_organizer.log`
- **Unorganized Folder**: Files without sufficient metadata are placed in `unorganized/` folder

## Installation

### Prerequisites

- Python 3.7 or higher
- uv (fast Python package installer and virtual environment manager)

### Step 1: Install uv

If you don't have uv installed, install it:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Or using homebrew (macOS)
brew install uv
```

For more installation options, see [uv documentation](https://github.com/astral-sh/uv).

### Step 2: Create Virtual Environment

Navigate to the project directory and create a virtual environment:

```bash
cd /path/to/music_organizer_tool
uv venv
```

This creates a virtual environment in the `.venv` directory.

### Step 3: Activate Virtual Environment

```bash
# On Linux/macOS
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt.

### Step 4: Install Dependencies

With the virtual environment activated, install dependencies using uv:

```bash
uv pip install -r requirements.txt
```

This will install:
- `mutagen` - Audio metadata handling
- `pyacoustid` - Audio fingerprinting
- `musicbrainzngs` - MusicBrainz API client
- Supporting libraries

### Optional: Get AcoustID API Key

For automatic metadata recognition of untagged files, you'll need a free AcoustID API key:

1. Visit https://acoustid.org/api-key
2. Create a free account
3. Generate an API key
4. Use it with the `--acoustid-key` option

## Usage

### Basic Syntax

**Important**: Always activate the virtual environment before running the script:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Then run the script
python music_organizer.py SOURCE_DIR DEST_DIR [OPTIONS]
```

### Arguments

- `SOURCE_DIR`: Directory containing your music files (will be scanned recursively)
- `DEST_DIR`: Directory where organized music will be placed

### Options

- `--dryrun`: Preview changes without actually moving files (RECOMMENDED for first run)
- `--move`: Move files instead of copying (for in-place reorganization; can use same directory for source and dest)
- `--acoustid-key KEY`: AcoustID API key for identifying untagged files
- `--verbose`, `-v`: Enable verbose logging output
- `--help`, `-h`: Show help message

### Examples

#### 1. Preview organization (dry run)

**Always run with --dryrun first to preview changes:**

```bash
source .venv/bin/activate
python music_organizer.py /path/to/music /path/to/organized --dryrun
```

This will show you exactly what would happen without actually moving any files.

#### 2. Organize music with existing metadata only

```bash
source .venv/bin/activate
python music_organizer.py /path/to/music /path/to/organized
```

This organizes files based on their embedded metadata tags. Files without sufficient metadata go to `unorganized/` folder.

#### 3. Organize with automatic metadata recognition

```bash
source .venv/bin/activate
python music_organizer.py /path/to/music /path/to/organized --acoustid-key YOUR_API_KEY
```

This attempts to identify untagged files using audio fingerprinting.

#### 4. Organize with verbose output

```bash
source .venv/bin/activate
python music_organizer.py /path/to/music /path/to/organized --verbose
```

Shows detailed logging information during the process.

#### 5. In-place reorganization (move mode)

```bash
source .venv/bin/activate
# Preview in-place reorganization
python music_organizer.py ~/Music ~/Music --move --dryrun

# Actually reorganize in place
python music_organizer.py ~/Music ~/Music --move
```

This moves files within the same directory, reorganizing them in place. Files already in the correct location are skipped. This is ideal for automated cron jobs that keep your music folder organized.

## Output Structure

The tool organizes music into the following structure:

```
organized_music/
├── Artist Name 1/
│   ├── Album Name 1/
│   │   ├── cover.jpg
│   │   ├── 01 - Track Name.mp3
│   │   ├── 02 - Track Name.mp3
│   │   └── ...
│   └── Album Name 2/
│   │   ├── cover.png
│   │   └── ...
├── Artist Name 2/
│   └── ...
└── unorganized/
    ├── unknown_song1.mp3
    └── unknown_song2.mp3
```

### Organized Files

Files with sufficient metadata (Artist, Album, Title) are organized into:
```
Artist/Album/[TrackNumber -] Title.extension
```

### Album Art Handling

The tool automatically manages album art:

- **Detects image files** (`.jpg`, `.jpeg`, `.png`) in source directories
- **Copies to album folders** and renames to `cover.jpg` (or `cover.png`)
- **Preserves existing art** - if `cover.jpg` already exists in the destination, it's kept
- **One per album** - only copies album art once per source directory
- **Common formats supported**: Works with files like `AlbumArt_{GUID}_Large.jpg`, `folder.jpg`, etc.

Album art is handled when organizing audio files, so each organized album folder gets the artwork from its source directory.

### Unorganized Files

Files without sufficient metadata are placed in:
```
unorganized/original_filename.extension
```

You can later manually tag these files or use the AcoustID feature to identify them.

## Workflow Recommendations

### First Time Setup

1. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Test with dry run:**
   ```bash
   python music_organizer.py /path/to/music /path/to/organized --dryrun
   ```

3. **Review the preview output** to ensure the organization looks correct

4. **Run the actual organization:**
   ```bash
   python music_organizer.py /path/to/music /path/to/organized
   ```

5. **Check the unorganized folder** for files without metadata

6. **Re-run with AcoustID** to identify untagged files:
   ```bash
   python music_organizer.py /path/to/music /path/to/organized --acoustid-key YOUR_KEY
   ```

### Regular Maintenance

For ongoing music organization, you can:
- Set up a cron job to run the script nightly (see [CRON_SETUP.md](CRON_SETUP.md))
- Point the script at a "downloads" or "incoming" folder
- Have it organize new music automatically

## Logging

The tool creates a log file `music_organizer.log` in the current directory with detailed information about:
- Files processed
- Metadata found
- Files moved/copied
- Album art copied
- Errors encountered
- AcoustID matches

Review this log file if you need to troubleshoot issues.

## Statistics Summary

After each run, the tool displays a summary:

```
============================================================
ORGANIZATION SUMMARY
============================================================
Total files processed: 150
Successfully organized: 142
Moved to unorganized/: 8
Already in correct location (skipped): 12
Album art copied: 35
Metadata found via AcoustID: 5
Errors: 0
============================================================
```

## Supported Audio Formats

- MP3 (`.mp3`)
- FLAC (`.flac`)
- M4A/MP4 (`.m4a`, `.mp4`)
- OGG Vorbis (`.ogg`)
- Opus (`.opus`)
- Windows Media Audio (`.wma`)
- WAV (`.wav`)
- AAC (`.aac`)

## Important Notes

### File Safety

- The tool **copies** files rather than moving them, so your original files remain untouched
- Always run with `--dryrun` first to preview changes
- Keep backups of your music collection before running any organization tool

### Metadata Requirements

For a file to be properly organized, it needs:
- Artist (or Album Artist)
- Album
- Title

Optional but recommended:
- Track Number (for proper sorting)

### AcoustID Rate Limiting

The AcoustID API has rate limits:
- Free tier: 3 requests per second
- The tool processes files sequentially to respect these limits
- Large collections may take time to process

### Filename Sanitization

The tool automatically sanitizes filenames by:
- Removing invalid characters (`<>:"/\|?*`)
- Limiting filename length to 200 characters
- Replacing multiple spaces with single spaces
- Using "Unknown" for empty values

## Troubleshooting

### Missing Dependencies Error

If you see `ModuleNotFoundError`, ensure you've activated the virtual environment and installed dependencies:
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

### AcoustID Errors

If AcoustID identification fails:
- Verify your API key is correct
- Check your internet connection
- Check the logs for specific error messages
- The tool will continue and place unidentified files in `unorganized/`

### Permission Errors

If you get permission errors:
- Ensure you have read access to source directory
- Ensure you have write access to destination directory
- On Linux/Mac, check file permissions with `ls -la`

### Files Not Being Organized

If files aren't being organized:
- Check that they have a supported audio extension
- Verify the files have metadata tags (use a tool like Mp3tag or MusicBrainz Picard)
- Check the log file for specific errors
- Run with `--verbose` for detailed output

## See Also

- [CRON_SETUP.md](CRON_SETUP.md) - Guide for setting up automatic nightly organization
- [MusicBrainz Picard](https://picard.musicbrainz.org/) - Recommended tool for tagging music files
- [AcoustID](https://acoustid.org/) - Audio fingerprinting service

## License

This tool is provided as-is for personal use.
