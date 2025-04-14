#!/bin/bash

# process-playlists.sh
# This script processes all playlist Excel files in the _playlists directory,
# copies the necessary albums to the SDXC card, and creates M3U playlists.

# Configuration
PYTHON_DIR="./_python"
PLAYLISTS_DIR="./_playlists"
PYTHON_SCRIPT="$PYTHON_DIR/process-playlists.py"

echo "=== A&K SP3000 Playlist Processor ==="
echo "This script will process all playlist Excel files, copy albums, and create M3U playlists"

# Check if SDXC card is mounted
if ! mountpoint -q "/mnt/sdcard"; then
    echo "Error: SDXC card not mounted at /mnt/sdcard"
    echo "Please mount your SDXC card and try again"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT"
    echo "Creating Python script directory..."
    mkdir -p "$PYTHON_DIR"
    
    # Check if the source script is in the current directory
    if [ -f "./process-playlists.py" ]; then
        echo "Moving process-playlists.py to $PYTHON_DIR..."
        cp "./process-playlists.py" "$PYTHON_SCRIPT"
        chmod +x "$PYTHON_SCRIPT"
    else
        echo "Error: Could not find process-playlists.py to copy to $PYTHON_DIR"
        exit 1
    fi
fi

# Check if playlists directory exists
if [ ! -d "$PLAYLISTS_DIR" ]; then
    echo "Error: Playlists directory not found at $PLAYLISTS_DIR"
    exit 1
fi

# Check if there are any Excel files in the playlists directory
PLAYLIST_COUNT=$(find "$PLAYLISTS_DIR" -maxdepth 1 -name "*.xlsx" | wc -l)
if [ "$PLAYLIST_COUNT" -eq 0 ]; then
    echo "Error: No playlist Excel files found in $PLAYLISTS_DIR"
    exit 1
fi

echo "Found $PLAYLIST_COUNT playlist Excel files in $PLAYLISTS_DIR"

# Make sure Python script is executable
chmod +x "$PYTHON_SCRIPT"

# Run the Python script to process all playlists
echo "Running Python script to process playlists..."
python3 "$PYTHON_SCRIPT" "$PLAYLISTS_DIR"

# Check exit status
if [ $? -eq 0 ]; then
    echo "Playlist processing completed successfully"
    echo "M3U playlists have been created in /mnt/sdcard/Playlists/"
    
    # List created playlists
    echo "Created playlists:"
    find /mnt/sdcard/Playlists -name "*.m3u" -printf "  - %f\n" | sort
else
    echo "Error occurred during playlist processing"
    exit 1
fi

echo "Your playlists are now ready to use on your A&K SP3000 player!"
