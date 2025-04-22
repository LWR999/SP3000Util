#!/bin/bash

# Check if a device parameter was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <device_partition> (e.g. /dev/sdc1)"
    exit 1
fi

DEVICE="$1"
MOUNT_POINT=""

# Check if the device exists
if [ ! -b "$DEVICE" ]; then
    echo "Error: Device $DEVICE does not exist or is not a block device"
    exit 1
fi

# Check if the device is mounted
if grep -q "$DEVICE" /proc/mounts; then
    # Get the mount point
    MOUNT_POINT=$(grep "$DEVICE" /proc/mounts | awk '{print $2}')
    echo "Device $DEVICE is already mounted at $MOUNT_POINT"
else
    # Create a temporary mount point
    MOUNT_POINT=$(mktemp -d)
    echo "Mounting $DEVICE to $MOUNT_POINT"
    
    # Try to mount the device
    if ! mount "$DEVICE" "$MOUNT_POINT"; then
        echo "Error: Failed to mount $DEVICE"
        rmdir "$MOUNT_POINT"
        exit 1
    fi
fi

# Initialize counters
total_deleted=0

# Function to safely delete files and count them
safe_delete() {
    local count=0
    local find_cmd="$1"
    local desc="$2"
    
    echo "Searching for $desc..."
    
    # First count the files
    count=$(eval "$find_cmd -type f | wc -l")
    
    if [ "$count" -gt 0 ]; then
        echo "Found $count $desc"
        
        # Delete the files
        eval "$find_cmd -type f -print -delete"
        total_deleted=$((total_deleted + count))
    else
        echo "No $desc found"
    fi
}

# Function to safely delete directories and count their contents
safe_delete_dir() {
    local count=0
    local find_cmd="$1"
    local desc="$2"
    
    echo "Searching for $desc..."
    
    # First count the files inside target directories
    count=$(eval "$find_cmd -type d | xargs -I{} find {} -type f | wc -l")
    
    # Find target directories
    dirs=$(eval "$find_cmd -type d")
    
    if [ -n "$dirs" ]; then
        echo "Found $desc containing $count files"
        
        # Delete the directories
        eval "$find_cmd -type d -print -exec rm -rf {} \;"
        total_deleted=$((total_deleted + count))
    else
        echo "No $desc found"
    fi
}

echo "Starting cleanup process on $MOUNT_POINT..."

# Delete "Artwork" or "artwork" folders
safe_delete_dir "find \"$MOUNT_POINT\" -name \"Artwork\" -o -name \"artwork\"" "artwork directories"

# Delete hidden files (starting with ".")
safe_delete "find \"$MOUNT_POINT\" -name \".*\"" "hidden files"

# Delete files with specified extensions (jpg, txt, log, url, png)
safe_delete "find \"$MOUNT_POINT\" -name \"*.jpg\" -o -name \"*.txt\" -o -name \"*.log\" -o -name \"*.url\" -o -name \"*.png\"" "files with specified extensions"

# Delete Mac Finder metadata files
safe_delete "find \"$MOUNT_POINT\" -name \".DS_Store\" -o -name \"._*\"" "Mac Finder metadata files"

echo "Cleanup complete. Total files deleted: $total_deleted"

# Unmount the device
echo "Unmounting $DEVICE from $MOUNT_POINT"
if umount "$DEVICE"; then
    echo "$DEVICE successfully unmounted"
    
    # Remove the temp directory if we created it
    if ! grep -q "$DEVICE" /proc/mounts; then
        rmdir "$MOUNT_POINT"
    fi
else
    echo "Error: Failed to unmount $DEVICE. May be in use."
    exit 1
fi

exit 0
