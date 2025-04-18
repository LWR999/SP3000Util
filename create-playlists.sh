#!/bin/bash

# create-playlists.sh
# Wrapper script to create playlists on the SDXC card
# Calls playlist-generator.py in the _python directory

# Usage: ./create-playlists.sh [device]
# Example: ./create-playlists.sh /dev/sdc1

# Configuration
PYTHON_DIR="./_python"
LIBRARY_DIR="./_library"
TRACKS_FILE="$LIBRARY_DIR/LibraryTracks.xlsx"
MOUNT_DIR="$HOME/SP3000Util/mnt"

echo "=== A&K SP3000 Playlist Creation Utility ==="
echo "This script will create DJ-like flow-optimized playlists on your SDXC card"

# Check for device parameter
if [ $# -eq 0 ]; then
  # No device parameter provided
  if ! mountpoint -q "$MOUNT_DIR"; then
    echo "Error: No device specified and no SD card mounted at $MOUNT_DIR"
    echo "Usage: $0 [device]"
    echo "Example: $0 /dev/sdc1"
    exit 1
  fi
  echo "Using already mounted SD card at $MOUNT_DIR"
else
  DEVICE="$1"
  
  # Check if the device exists
  if [ ! -b "$DEVICE" ]; then
    echo "Error: Device $DEVICE does not exist or is not a block device"
    exit 1
  fi
  
  # Check if the device is already mounted
  MOUNT_POINT=$(findmnt -n -o TARGET "$DEVICE" 2>/dev/null)
  if [ -n "$MOUNT_POINT" ]; then
    if [ "$MOUNT_POINT" != "$MOUNT_DIR" ]; then
      echo "Device $DEVICE is already mounted at $MOUNT_POINT"
      echo "Please unmount it first or use the already mounted path"
      exit 1
    else
      echo "Device $DEVICE is already mounted at $MOUNT_DIR"
    fi
  else
    # Create mount directory if it doesn't exist
    mkdir -p "$MOUNT_DIR"
    
    # Mount the device
    echo "Mounting $DEVICE to $MOUNT_DIR..."
    if ! mount "$DEVICE" "$MOUNT_DIR"; then
      echo "Error: Failed to mount $DEVICE to $MOUNT_DIR"
      echo "You might need to configure /etc/fstab or use udisksctl to allow mounting without sudo"
      exit 1
    fi
    echo "Device $DEVICE mounted successfully to $MOUNT_DIR"
  fi
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

# Create Music directory structure if it doesn't exist
echo "Ensuring Music directory structure exists..."
mkdir -p "$MOUNT_DIR/Music/CD"
mkdir -p "$MOUNT_DIR/Music/Hires"
mkdir -p "$MOUNT_DIR/Music/Playlists"

# Check if there are any music files on the SDXC card
MUSIC_COUNT=$(find "$MOUNT_DIR/Music" -type f -name "*.flac" -o -name "*.mp3" | wc -l)
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

# Make sure Python script is executable
chmod +x "$PYTHON_DIR/playlist-generator.py"

# Run the Python script
echo "Running playlist-generator.py to create playlists..."
python3 "$PYTHON_DIR/playlist-generator.py" "$TRACKS_FILE" "$MOUNT_DIR"

# Check if playlists were created
PLAYLIST_COUNT=$(find "$MOUNT_DIR/Music/Playlists" -name "*.m3u" | wc -l)
if [ "$PLAYLIST_COUNT" -gt 0 ]; then
    echo "Successfully created $PLAYLIST_COUNT playlists on your SDXC card"
    echo "Playlists are located in: $MOUNT_DIR/Music/Playlists/"
    echo ""
    echo "Playlists created:"
    find "$MOUNT_DIR/Music/Playlists" -name "*.m3u" -printf "  - %f\n" | sort
else
    echo "Warning: No playlists were created"
    echo "Check for errors in the output above"
fi
