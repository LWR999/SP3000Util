#!/bin/bash

# create-playlists.sh
# Wrapper script to create playlists on the SDXC card
# Calls playlist-generator.py in the _python directory

# Configuration
PYTHON_DIR="./_python"
LIBRARY_DIR="./_library"
TRACKS_FILE="$LIBRARY_DIR/LibraryTracks.xlsx"

echo "=== A&K SP3000 Playlist Creation Utility ==="
echo "This script will create DJ-like flow-optimized playlists on your SDXC card"

# Check if SDXC card is mounted
if ! mountpoint -q "/mnt/sdcard"; then
    echo "Error: SDXC card not mounted at /mnt/sdcard"
    echo "Please mount your SDXC card and try again"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_DIR/playlist-generator.py" ]; then
    echo "Error: Python script not found at $PYTHON_DIR/playlist-generator.py"
    exit 1
fi

# Check if library file exists
if [ ! -f "$TRACKS_FILE" ]; then
    echo "Error: Library tracks file not found at $TRACKS_FILE"
    exit 1
fi

# Make sure Python script is executable
chmod +x "$PYTHON_DIR/playlist-generator.py"

# Check if there are any music files on the SDXC card
MUSIC_COUNT=$(find /mnt/sdcard -type f -name "*.flac" -o -name "*.mp3" | wc -l)
if [ "$MUSIC_COUNT" -eq 0 ]; then
    echo "Warning: No music files found on the SDXC card"
    echo "Make sure you've copied music to the card before creating playlists"
    echo "Run fill-sdxc.sh and fill_remaining_space.sh first"
    
    # Ask if user wants to continue anyway
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create playlist directory if it doesn't exist
mkdir -p /mnt/sdcard/Playlists

# Run the Python script
echo "Running playlist-generator.py to create playlists..."
python3 "$PYTHON_DIR/playlist-generator.py" "$TRACKS_FILE"

# Check if playlists were created
PLAYLIST_COUNT=$(find /mnt/sdcard/Playlists -name "*.m3u" | wc -l)
if [ "$PLAYLIST_COUNT" -gt 0 ]; then
    echo "Successfully created $PLAYLIST_COUNT playlists on your SDXC card"
    echo "Playlists are located in: /mnt/sdcard/Playlists/"
    echo ""
    echo "Playlists created:"
    find /mnt/sdcard/Playlists -name "*.m3u" -printf "  - %f\n" | sort
else
    echo "Warning: No playlists were created"
    echo "Check for errors in the output above"
fi
