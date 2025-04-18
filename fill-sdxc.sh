#!/bin/bash

# fill-sdxc.sh
# Wrapper script to fill the SDXC card with music
# Calls tracks-filler.py in the _python directory

# Usage: ./fill-sdxc.sh [device]
# Example: ./fill-sdxc.sh /dev/sdc1

# Configuration
PYTHON_DIR="./_python"
LIBRARY_DIR="./_library"
TRACKS_FILE="$LIBRARY_DIR/LibraryTracks.xlsx"
MOUNT_DIR="$HOME/SP3000Util/mnt"

echo "=== A&K SP3000 SDXC Card Fill Utility ==="

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
if [ ! -f "$PYTHON_DIR/tracks-filler.py" ]; then
    echo "Error: Python script not found at $PYTHON_DIR/tracks-filler.py"
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

# Make sure Python script is executable
chmod +x "$PYTHON_DIR/tracks-filler.py"

# Run the Python script
echo "Running tracks-filler.py to analyze library and generate copy script..."
python3 "$PYTHON_DIR/tracks-filler.py" "$TRACKS_FILE" "$MOUNT_DIR"

# Check if the script was generated successfully
if [ -f "./fill_remaining_space.sh" ]; then
    echo "Successfully generated fill_remaining_space.sh"
    echo ""
    echo "To fill your SDXC card with music, run the following command:"
    echo "./fill_remaining_space.sh"
    chmod +x ./fill_remaining_space.sh
else
    echo "Error: Failed to generate fill_remaining_space.sh"
    exit 1
fi
