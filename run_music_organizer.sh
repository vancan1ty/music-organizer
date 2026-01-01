#!/bin/bash

# Music Organizer Nightly Run Script
# This script is designed to be run by cron

# Exit on error
set -e

# Set up logging
LOG_DIR="$HOME/logs/music_organizer"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d_%H%M%S).log"

# Redirect all output to log file
exec > "$LOG_FILE" 2>&1

echo "========================================"
echo "Music Organizer - Started at $(date)"
echo "========================================"

# Get the directory where this script is located
SCRIPT_DIR_DEFAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Detected script directory: $SCRIPT_DIR_DEFAULT"

# Load configuration from .env file
ENV_FILE="${SCRIPT_DIR:-$SCRIPT_DIR_DEFAULT}/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: Configuration file not found: $ENV_FILE"
    echo "Please create a .env file based on .env.example"
    exit 1
fi

echo "Loading configuration from $ENV_FILE"
source "$ENV_FILE"

# Change to script directory
cd "$SCRIPT_DIR"

# Activate virtual environment (required)
echo "Activating virtual environment..."
source .venv/bin/activate

# Verify Python is using the venv
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"

# Run the organizer in-place with move mode
# Using same directory for source and dest with --move flag for in-place reorganization
python music_organizer.py "$MUSIC_DIR" "$MUSIC_DIR" --move --acoustid-key "$ACOUSTID_KEY"

# Exit code
EXIT_CODE=$?

echo "========================================"
echo "Music Organizer - Finished at $(date)"
echo "Exit code: $EXIT_CODE"
echo "========================================"

# Clean up old log files (keep last 30 days)
find "$LOG_DIR" -name "cron_*.log" -mtime +30 -delete

exit $EXIT_CODE
