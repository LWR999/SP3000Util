#!/bin/bash
#
# rebuild-sdxc.sh
# Purpose: Rebuild an SDXC card from a snapshot file
# Usage: ./rebuild-sdxc.sh <device_partition> <snapshot_file> [resume]
# Example: ./rebuild-sdxc.sh /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_20250422_120000.txt
# Example with resume: ./rebuild-sdxc.sh /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_20250422_120000.txt resume
#
# This script:
# - Mounts the SD card if not already mounted
# - Reads album paths from the snapshot file
# - Optionally erases the card (if not in resume mode)
# - Copies the specified albums from server to SD card
# - Uses rsync for efficient copying and resuming
#

# Define paths
# Handle sudo correctly by getting the real user's home directory
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
    REAL_HOME=$(eval echo ~$REAL_USER)
else
    REAL_USER="$USER"
    REAL_HOME="$HOME"
fi

MOUNT_POINT="$REAL_HOME/SP3000Util/mnt"
MUSIC_DIR="$MOUNT_POINT/Music"

# Create mount point with proper ownership if running as sudo
if [ -n "$SUDO_USER" ]; then
    mkdir -p "$MOUNT_POINT"
    chown -R "$REAL_USER":"$REAL_USER" "$MOUNT_POINT"
fi

# Check if required parameters were provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <device_partition> <snapshot_file> [resume]"
    echo "Example: $0 /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_20250422_120000.txt"
    echo "Example with resume: $0 /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_20250422_120000.txt resume"
    exit 1
fi

DEVICE="$1"
SNAPSHOT_FILE="$2"
RESUME_MODE=0

# Check if resume parameter was provided
if [ $# -eq 3 ] && [ "$3" = "resume" ]; then
    RESUME_MODE=1
    echo "Running in resume mode. Will not erase card."
fi

# Check if the device exists
if [ ! -b "$DEVICE" ]; then
    echo "Error: Device $DEVICE does not exist or is not a block device"
    exit 1
fi

# Check if the snapshot file exists
if [ ! -f "$SNAPSHOT_FILE" ]; then
    echo "Error: Snapshot file $SNAPSHOT_FILE does not exist"
    exit 1
fi

# Function to handle mounting
mount_device() {
    # Create mount point if it doesn't exist
    mkdir -p "$MOUNT_POINT"
    
    # Check if already mounted
    if grep -q "$DEVICE" /proc/mounts; then
        # Get the current mount point
        CURRENT_MOUNT=$(grep "$DEVICE" /proc/mounts | awk '{print $2}')
        
        if [ "$CURRENT_MOUNT" != "$MOUNT_POINT" ]; then
            echo "Device is already mounted at $CURRENT_MOUNT, which is different from $MOUNT_POINT"
            echo "Please unmount it first: sudo umount $CURRENT_MOUNT"
            exit 1
        else
            echo "Device $DEVICE is already mounted at $MOUNT_POINT"
        fi
    else
        echo "Mounting $DEVICE to $MOUNT_POINT"
        # Try udisksctl first (avoids sudo if properly configured)
        if command -v udisksctl &>/dev/null; then
            udisksctl mount -b "$DEVICE" --mount-options "uid=$(id -u),gid=$(id -g)" 2>/dev/null
            
            # Check if mount was successful
            if ! grep -q "$DEVICE" /proc/mounts; then
                # Fall back to regular mount
                echo "udisksctl mount failed, trying regular mount..."
                if ! mount "$DEVICE" "$MOUNT_POINT"; then
                    echo "Error: Failed to mount $DEVICE. Try manually: sudo mount $DEVICE $MOUNT_POINT"
                    exit 1
                fi
            fi
        else
            # Use regular mount
            if ! mount "$DEVICE" "$MOUNT_POINT"; then
                echo "Error: Failed to mount $DEVICE. Try manually: sudo mount $DEVICE $MOUNT_POINT"
                exit 1
            fi
        fi
        
        echo "Successfully mounted $DEVICE at $MOUNT_POINT"
    fi
}

# Function to prepare card
prepare_card() {
    # Create directory structure if needed
    mkdir -p "$MUSIC_DIR/CD"
    mkdir -p "$MUSIC_DIR/Hires"
    mkdir -p "$MUSIC_DIR/Playlists"
    
    # If not in resume mode, erase contents of CD and Hires
    if [ $RESUME_MODE -eq 0 ]; then
        echo "Erasing contents of CD and Hires directories..."
        rm -rf "$MUSIC_DIR/CD/"*
        rm -rf "$MUSIC_DIR/Hires/"*
        echo "Erasure complete."
    else
        echo "In resume mode. Keeping existing files."
    fi
}

# Function to validate snapshot file
validate_snapshot() {
    echo "Validating snapshot file..."
    
    # Check if file has content
    if [ ! -s "$SNAPSHOT_FILE" ]; then
        echo "Error: Snapshot file is empty"
        exit 1
    fi
    
    # Count CD and HiRes entries
    cd_count=$(grep -c "^CD|" "$SNAPSHOT_FILE")
    hires_count=$(grep -c "^HIRES|" "$SNAPSHOT_FILE")
    
    if [ $cd_count -eq 0 ] && [ $hires_count -eq 0 ]; then
        echo "Error: No valid album entries found in snapshot file"
        exit 1
    fi
    
    echo "Snapshot file contains $cd_count CD albums and $hires_count HiRes albums"
}

# Function to copy albums from snapshot
copy_albums() {
    echo "Starting album copy process..."
    
    total_count=0
    success_count=0
    
    # Process each line in the snapshot file
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ "$line" =~ ^#.*$ ]] || [[ -z "$line" ]]; then
            continue
        fi
        
        # Extract type and path
        type=$(echo "$line" | cut -d'|' -f1)
        path=$(echo "$line" | cut -d'|' -f2)
        album_name=$(basename "$path")
        
        # Increment total count
        ((total_count++))
        
        # Skip if path doesn't exist
        if [ ! -d "$path" ]; then
            echo "Warning: Source path does not exist: $path"
            continue
        fi
        
        # Determine destination directory
        if [ "$type" = "CD" ]; then
            dest_dir="$MUSIC_DIR/CD/$album_name"
        elif [ "$type" = "HIRES" ]; then
            dest_dir="$MUSIC_DIR/Hires/$album_name"
        else
            echo "Warning: Unknown type '$type' for path: $path"
            continue
        fi
        
        # Create destination directory if it doesn't exist
        mkdir -p "$dest_dir"
        
        # Copy files using rsync
        echo "Copying $type album: $album_name"
        if rsync -av --progress "$path/" "$dest_dir/" --exclude ".*" --exclude "*.jpg" --exclude "*.png" --exclude "*.txt" --exclude "*.log" --exclude "*.url" --exclude "Artwork/" --exclude "artwork/"; then
            ((success_count++))
            echo "Successfully copied $album_name"
        else
            echo "Error copying $album_name"
        fi
        
        # Add a blank line for separation
        echo ""
    done < "$SNAPSHOT_FILE"
    
    echo "Copy process complete."
    echo "Successfully copied $success_count of $total_count albums."
}

# Main execution
echo "Starting SDXC rebuild process for device $DEVICE using snapshot $SNAPSHOT_FILE"

# Step 1: Mount the device
mount_device

# Step 2: Validate snapshot file
validate_snapshot

# Step 3: Prepare the card
prepare_card

# Step 4: Copy albums
copy_albums

echo "Rebuild process complete!"
echo ""
echo "To unmount the card:"
echo "sudo umount $MOUNT_POINT"
echo ""
echo "Next steps:"
echo "1. Run ./create-playlists.sh to rebuild playlists"
echo "2. Run ./declutter.sh $DEVICE (if needed to clean up any remaining clutter files)"

exit 0
