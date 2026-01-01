#!/usr/bin/env python3
"""
Music Organizer Tool
Organizes music files into a systematic Artist/Album/Track structure.
Supports metadata recognition via AcoustID and MusicBrainz for untagged files.
"""

import os
import sys
import argparse
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    import acoustid
    import musicbrainzngs
except ImportError as e:
    print(f"Error: Missing required library: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('music_organizer.log')
    ]
)
logger = logging.getLogger(__name__)

# Configure MusicBrainz
musicbrainzngs.set_useragent("MusicOrganizerTool", "1.0", "https://github.com/yourusername/music-organizer")

# Supported audio file extensions
AUDIO_EXTENSIONS = {'.mp3', '.flac', '.m4a', '.mp4', '.ogg', '.opus', '.wma', '.wav', '.aac'}

# Supported image file extensions for album art
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}


class MusicOrganizer:
    """Main class for organizing music files."""

    def __init__(self, source_dir: str, dest_dir: str, dry_run: bool = False,
                 acoustid_api_key: Optional[str] = None, move_files: bool = False):
        """
        Initialize the Music Organizer.

        Args:
            source_dir: Source directory containing music files
            dest_dir: Destination directory for organized music
            dry_run: If True, preview changes without making them
            acoustid_api_key: API key for AcoustID service (optional)
            move_files: If True, move files instead of copying them (for in-place reorganization)
        """
        self.source_dir = Path(source_dir).resolve()
        self.dest_dir = Path(dest_dir).resolve()
        self.dry_run = dry_run
        self.acoustid_api_key = acoustid_api_key
        self.move_files = move_files
        self.processed_album_art_dirs = set()  # Track dirs we've already processed album art for
        self.stats = {
            'total_files': 0,
            'organized': 0,
            'unorganized': 0,
            'metadata_found': 0,
            'errors': 0,
            'skipped': 0,
            'album_art_copied': 0
        }

    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename to be filesystem-safe.

        Args:
            name: Original filename or path component

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace multiple spaces with single space
        name = re.sub(r'\s+', ' ', name)
        # Strip leading/trailing whitespace and dots
        name = name.strip('. ')
        # Limit length
        if len(name) > 200:
            name = name[:200]
        return name if name else 'Unknown'

    def get_metadata(self, file_path: Path) -> Dict[str, str]:
        """
        Extract metadata from audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with artist, album, title, track number
        """
        try:
            audio = MutagenFile(str(file_path), easy=True)
            if audio is None:
                return {}

            metadata = {}

            # Try to get common tags (works for most formats via mutagen's easy interface)
            if hasattr(audio, 'tags') and audio.tags:
                # Get artist
                for key in ['artist', 'albumartist', 'TPE1', 'TPE2', '©ART', 'ARTIST']:
                    if key in audio:
                        metadata['artist'] = str(audio[key][0]) if isinstance(audio[key], list) else str(audio[key])
                        break

                # Get album
                for key in ['album', 'TALB', '©alb', 'ALBUM']:
                    if key in audio:
                        metadata['album'] = str(audio[key][0]) if isinstance(audio[key], list) else str(audio[key])
                        break

                # Get title
                for key in ['title', 'TIT2', '©nam', 'TITLE']:
                    if key in audio:
                        metadata['title'] = str(audio[key][0]) if isinstance(audio[key], list) else str(audio[key])
                        break

                # Get track number
                for key in ['tracknumber', 'TRCK', 'trkn', 'TRACKNUMBER']:
                    if key in audio:
                        track = str(audio[key][0]) if isinstance(audio[key], list) else str(audio[key])
                        # Extract just the number if it's in format "1/10"
                        metadata['track'] = track.split('/')[0].zfill(2)
                        break

            return metadata

        except Exception as e:
            logger.warning(f"Error reading metadata from {file_path}: {e}")
            return {}

    def get_metadata_from_acoustid(self, file_path: Path) -> Optional[Dict[str, str]]:
        """
        Try to identify audio file using AcoustID and MusicBrainz.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with metadata or None if not found
        """
        if not self.acoustid_api_key:
            logger.debug("AcoustID API key not provided, skipping acoustic fingerprinting")
            return None

        try:
            logger.info(f"Attempting to identify {file_path.name} using AcoustID...")

            # Get acoustic fingerprint and duration
            results = acoustid.match(self.acoustid_api_key, str(file_path))

            for score, recording_id, title, artist in results:
                if score > 0.5:  # Confidence threshold
                    logger.info(f"Match found with {score:.0%} confidence: {artist} - {title}")

                    # Try to get more metadata from MusicBrainz
                    try:
                        recording = musicbrainzngs.get_recording_by_id(
                            recording_id,
                            includes=['artists', 'releases']
                        )

                        metadata = {
                            'title': title,
                            'artist': artist
                        }

                        # Get album from first release
                        if 'release-list' in recording['recording']:
                            releases = recording['recording']['release-list']
                            if releases:
                                metadata['album'] = releases[0]['title']

                        self.stats['metadata_found'] += 1
                        return metadata

                    except Exception as e:
                        logger.warning(f"Error fetching MusicBrainz data: {e}")
                        # Return what we have
                        return {'title': title, 'artist': artist}

            logger.info(f"No confident match found for {file_path.name}")
            return None

        except Exception as e:
            logger.warning(f"Error identifying {file_path}: {e}")
            return None

    def get_destination_path(self, file_path: Path, metadata: Dict[str, str]) -> Path:
        """
        Determine destination path based on metadata.

        Args:
            file_path: Original file path
            metadata: Metadata dictionary

        Returns:
            Destination path
        """
        # Check if we have enough metadata
        if 'artist' in metadata and 'album' in metadata and 'title' in metadata:
            artist = self.sanitize_filename(metadata['artist'])
            album = self.sanitize_filename(metadata['album'])
            title = self.sanitize_filename(metadata['title'])

            # Build filename with track number if available
            if 'track' in metadata:
                filename = f"{metadata['track']} - {title}{file_path.suffix}"
            else:
                filename = f"{title}{file_path.suffix}"

            # Build path: Artist/Album/Track
            dest_path = self.dest_dir / artist / album / filename

        else:
            # Not enough metadata, put in unorganized folder
            dest_path = self.dest_dir / 'unorganized' / file_path.name

        return dest_path

    def copy_album_art(self, source_dir: Path, dest_album_dir: Path) -> None:
        """
        Copy album art from source directory to destination album directory.

        Args:
            source_dir: Source directory containing the original audio file
            dest_album_dir: Destination album directory where art should be copied
        """
        # Skip if we've already processed this source directory
        source_dir_key = str(source_dir.resolve())
        if source_dir_key in self.processed_album_art_dirs:
            return

        # Mark this directory as processed
        self.processed_album_art_dirs.add(source_dir_key)

        # Check if destination already has cover art
        existing_cover = None
        for ext in ['.jpg', '.jpeg', '.png']:
            potential_cover = dest_album_dir / f'cover{ext}'
            if potential_cover.exists():
                existing_cover = potential_cover
                break

        if existing_cover:
            logger.debug(f"Album art already exists at {existing_cover}, skipping")
            return

        # Look for image files in source directory
        image_files = []
        try:
            for item in source_dir.iterdir():
                if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                    image_files.append(item)
        except Exception as e:
            logger.warning(f"Error scanning for album art in {source_dir}: {e}")
            return

        if not image_files:
            logger.debug(f"No album art found in {source_dir}")
            return

        # Use the first image file found
        source_image = image_files[0]
        dest_ext = source_image.suffix.lower()
        if dest_ext == '.jpeg':
            dest_ext = '.jpg'
        dest_image = dest_album_dir / f'cover{dest_ext}'

        # Copy the image
        if self.dry_run:
            logger.info(f"[DRY RUN] Would copy album art: {source_image} -> {dest_image}")
        else:
            try:
                if self.move_files:
                    shutil.copy2(str(source_image), str(dest_image))
                    logger.info(f"Copied album art: {source_image.name} -> {dest_image}")
                else:
                    shutil.copy2(str(source_image), str(dest_image))
                    logger.info(f"Copied album art: {source_image.name} -> {dest_image}")
                self.stats['album_art_copied'] += 1
            except Exception as e:
                logger.warning(f"Error copying album art from {source_image}: {e}")

    def organize_file(self, file_path: Path) -> bool:
        """
        Organize a single music file.

        Args:
            file_path: Path to music file

        Returns:
            True if successfully organized, False otherwise
        """
        try:
            logger.info(f"Processing: {file_path}")

            # Get metadata from file
            metadata = self.get_metadata(file_path)

            # If metadata is insufficient, try AcoustID
            if not all(k in metadata for k in ['artist', 'album', 'title']):
                logger.info(f"Insufficient metadata in file, trying AcoustID...")
                acoustid_metadata = self.get_metadata_from_acoustid(file_path)
                time.sleep(0.33)
                if acoustid_metadata:
                    metadata.update(acoustid_metadata)

            # Determine destination
            dest_path = self.get_destination_path(file_path, metadata)

            # Check if file is already in the correct location
            if file_path.resolve() == dest_path.resolve():
                logger.info(f"File already in correct location: {file_path}")
                self.stats['skipped'] += 1
                return True

            # In copy mode, skip if destination file already exists
            if not self.move_files and dest_path.exists():
                logger.info(f"File already exists at destination, skipping: {dest_path}")
                self.stats['skipped'] += 1
                return True

            # Check if file would go to unorganized
            if 'unorganized' in dest_path.parts:
                self.stats['unorganized'] += 1
                logger.warning(f"Insufficient metadata for {file_path.name}, moving to unorganized/")
            else:
                self.stats['organized'] += 1

            # Display action
            action_verb = "move" if self.move_files else "copy"
            if self.dry_run:
                logger.info(f"[DRY RUN] Would {action_verb}: {file_path} -> {dest_path}")
                # Also check for album art during dry run
                if 'unorganized' not in dest_path.parts:
                    source_dir = file_path.parent
                    dest_album_dir = dest_path.parent
                    self.copy_album_art(source_dir, dest_album_dir)
            else:
                # Create destination directory
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Move or copy file
                if self.move_files:
                    shutil.move(str(file_path), str(dest_path))
                    logger.info(f"Moved: {file_path} -> {dest_path}")
                else:
                    shutil.copy2(str(file_path), str(dest_path))
                    logger.info(f"Copied: {file_path} -> {dest_path}")

                # Copy album art if this file went to an organized album folder (not unorganized)
                if 'unorganized' not in dest_path.parts:
                    source_dir = file_path.parent
                    dest_album_dir = dest_path.parent
                    self.copy_album_art(source_dir, dest_album_dir)

            return True

        except Exception as e:
            logger.error(f"Error organizing {file_path}: {e}")
            self.stats['errors'] += 1
            return False

    def find_audio_files(self) -> List[Path]:
        """
        Recursively find all audio files in source directory.

        Returns:
            List of audio file paths
        """
        audio_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in AUDIO_EXTENSIONS:
                    audio_files.append(file_path)
        return audio_files

    def organize(self) -> None:
        """
        Main method to organize all music files.
        """
        logger.info(f"Starting music organization...")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Destination: {self.dest_dir}")
        logger.info(f"Mode: {'MOVE' if self.move_files else 'COPY'}")
        logger.info(f"Dry run: {self.dry_run}")

        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return

        if not self.dry_run:
            self.dest_dir.mkdir(parents=True, exist_ok=True)

        # Find all audio files
        logger.info("Scanning for audio files...")
        audio_files = self.find_audio_files()
        self.stats['total_files'] = len(audio_files)

        logger.info(f"Found {len(audio_files)} audio files")

        # Process each file
        for file_path in audio_files:
            self.organize_file(file_path)

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print summary statistics."""
        print("\n" + "="*60)
        print("ORGANIZATION SUMMARY")
        print("="*60)
        print(f"Total files processed: {self.stats['total_files']}")
        print(f"Successfully organized: {self.stats['organized']}")
        print(f"Moved to unorganized/: {self.stats['unorganized']}")
        print(f"Already in correct location (skipped): {self.stats['skipped']}")
        print(f"Album art copied: {self.stats['album_art_copied']}")
        print(f"Metadata found via AcoustID: {self.stats['metadata_found']}")
        print(f"Errors: {self.stats['errors']}")
        print("="*60)

        if self.dry_run:
            action = "moved" if self.move_files else "copied"
            print(f"\nThis was a DRY RUN - no files were actually {action}.")
            print("Run without --dryrun to apply changes.")
        elif self.move_files:
            print("\nFiles were MOVED (not copied) - originals have been relocated.")
        else:
            print("\nFiles were COPIED - originals remain in place.")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Organize music files into Artist/Album/Track structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/music /path/to/organized --dryrun
  %(prog)s /path/to/music /path/to/organized --acoustid-key YOUR_API_KEY
  %(prog)s /path/to/music /path/to/organized --move  # In-place reorganization
  %(prog)s ~/Music ~/Music --move --dryrun  # Preview in-place reorganization
        """
    )

    parser.add_argument(
        'source_dir',
        help='Source directory containing music files'
    )

    parser.add_argument(
        'dest_dir',
        help='Destination directory for organized music'
    )

    parser.add_argument(
        '--dryrun',
        action='store_true',
        help='Preview changes without actually moving files'
    )

    parser.add_argument(
        '--move',
        action='store_true',
        help='Move files instead of copying (for in-place reorganization)'
    )

    parser.add_argument(
        '--acoustid-key',
        help='AcoustID API key for audio fingerprinting (get one at https://acoustid.org/api-key)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create organizer and run
    organizer = MusicOrganizer(
        source_dir=args.source_dir,
        dest_dir=args.dest_dir,
        dry_run=args.dryrun,
        acoustid_api_key=args.acoustid_key,
        move_files=args.move
    )

    organizer.organize()


if __name__ == '__main__':
    main()
