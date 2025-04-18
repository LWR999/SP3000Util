#!/bin/bash

# process-playlists.sh
# This script processes all playlist Excel files in the _playlists directory,
# copies the necessary albums to the SDXC card, and creates M3U playlists.

# Usage: ./process-playlists.sh [device]
# Example: ./process-playlists.sh /dev/sdc1

# Configuration
PYTHON_DIR="./_python"
PLAYLISTS_DIR="./_playlists"
PYTHON_SCRIPT="$PYTHON_DIR/process-playlists.py"
MOUNT_DIR="$HOME/SP3000Util/mnt"

echo "=== A&K SP3000 Playlist Processor ==="
echo "This script will process all playlist Excel files, copy albums, and create M3U playlists"

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

# Create Music directory structure if it doesn't exist
echo "Ensuring Music directory structure exists..."
mkdir -p "$MOUNT_DIR/Music/CD"
mkdir -p "$MOUNT_DIR/Music/Hires"
mkdir -p "$MOUNT_DIR/Music/Playlists"

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
python3 "$PYTHON_SCRIPT" "$PLAYLISTS_DIR" "$MOUNT_DIR"

# Check exit status
if [ $? -eq 0 ]; then
    echo "Playlist processing completed successfully"
    echo "M3U playlists have been created in $MOUNT_DIR/Music/Playlists/"
    
    # List created playlists
    echo "Created playlists:"
    find "$MOUNT_DIR/Music/Playlists" -name "*.m3u" -printf "  - %f\n" | sort
else
    echo "Error occurred during playlist processing"
    exit 1
fi

echo "Your playlists are now ready to use on your A&K SP3000 player!"
