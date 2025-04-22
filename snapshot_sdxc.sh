#!/bin/bash
#
# snapshot-card.sh
# Purpose: Create a snapshot file of all album paths on an SDXC card
# Usage: ./snapshot-card.sh <device_partition>
# Example: ./snapshot-card.sh /dev/sdc1
#
# This script:
# - Mounts the SD card if not already mounted
# - Scans the current card to identify which albums are present
# - Creates a snapshot file with NAS paths for all albums
#

# Define paths
SERVER_CD_PATH="/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 16-Bit CD"
SERVER_HIRES_PATH="/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 24-Bit HiRes"

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
SNAPSHOTS_DIR="$REAL_HOME/SP3000Util/snapshots"

# Create directories with proper ownership if running as sudo
if [ -n "$SUDO_USER" ]; then
    mkdir -p "$MOUNT_POINT" "$SNAPSHOTS_DIR"
    chown -R "$REAL_USER":"$REAL_USER" "$MOUNT_POINT" "$SNAPSHOTS_DIR"
fi

# Check if device parameter was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <device_partition>"
    echo "Example: $0 /dev/sdc1"
    exit 1
fi

DEVICE="$1"

# Check if the device exists
if [ ! -b "$DEVICE" ]; then
    echo "Error: Device $DEVICE does not exist or is not a block device"
    exit 1
fi

# Create snapshots directory if it doesn't exist
mkdir -p "$SNAPSHOTS_DIR"

# Generate snapshot filename with date and time
SNAPSHOT_FILE="$SNAPSHOTS_DIR/sd_snap_$(date +%Y%m%d)_$(date +%H%M%S).txt"

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

# Function to scan the existing SD card structure and create snapshot
create_snapshot() {
    echo "Scanning existing SDXC card structure..."
    
    # Check if the Music directory exists
    if [ ! -d "$MUSIC_DIR" ]; then
        echo "Error: $MUSIC_DIR directory does not exist. Is the card mounted correctly?"
        exit 1
    fi
    
    # Check if CD and Hires directories exist
    if [ ! -d "$MUSIC_DIR/CD" ] || [ ! -d "$MUSIC_DIR/Hires" ]; then
        echo "Error: CD or Hires directory not found on the SDXC card."
        exit 1
    fi
    
    # Initialize the snapshot file with header
    echo "# SDXC Card Snapshot created $(date)" > "$SNAPSHOT_FILE"
    echo "# Device: $DEVICE" >> "$SNAPSHOT_FILE"
    echo "# " >> "$SNAPSHOT_FILE"
    echo "# Format: <type>|<NAS path>" >> "$SNAPSHOT_FILE"
    echo "# " >> "$SNAPSHOT_FILE"
    
    # Find and add CD albums to snapshot
    echo "Finding CD-quality albums..."
    cd_count=0
    
    while IFS= read -r album_path; do
        album_name=$(basename "$album_path")
        echo "CD|$SERVER_CD_PATH/$album_name" >> "$SNAPSHOT_FILE"
        ((cd_count++))
    done < <(find "$MUSIC_DIR/CD" -mindepth 1 -maxdepth 1 -type d | sort)
    
    # Find and add HiRes albums to snapshot
    echo "Finding HiRes albums..."
    hires_count=0
    
    while IFS= read -r album_path; do
        album_name=$(basename "$album_path")
        echo "HIRES|$SERVER_HIRES_PATH/$album_name" >> "$SNAPSHOT_FILE"
        ((hires_count++))
    done < <(find "$MUSIC_DIR/Hires" -mindepth 1 -maxdepth 1 -type d | sort)
    
    # Add summary to snapshot
    echo "# " >> "$SNAPSHOT_FILE"
    echo "# Summary: $cd_count CD albums, $hires_count HiRes albums" >> "$SNAPSHOT_FILE"
    echo "# Total: $((cd_count + hires_count)) albums" >> "$SNAPSHOT_FILE"
    
    echo "Snapshot created with $cd_count CD albums and $hires_count HiRes albums"
    echo "Snapshot file: $SNAPSHOT_FILE"
}

# Main execution
echo "Starting SDXC card snapshot process for device $DEVICE"

# Step 1: Mount the device
mount_device

# Step 2: Create snapshot
create_snapshot

echo "Snapshot process complete!"
echo ""
echo "Snapshot file created: $SNAPSHOT_FILE"
echo ""
echo "To unmount the card:"
echo "sudo umount $MOUNT_POINT"
echo ""
echo "To rebuild a card using this snapshot:"
echo "./rebuild-sdxc.sh <device> $SNAPSHOT_FILE [resume]"

exit 0
