#!/bin/bash

# fill-sdxc.sh
# Wrapper script to fill the SDXC card with music
# Calls tracks-filler.py in the _python directory

# Configuration
PYTHON_DIR="./_python"
LIBRARY_DIR="./_library"
TRACKS_FILE="$LIBRARY_DIR/LibraryTracks.xlsx"

echo "=== A&K SP3000 SDXC Card Fill Utility ==="
echo "This script will analyze your library and prepare to fill your SDXC card"

# Check if SDXC card is mounted
if ! mountpoint -q "/mnt/sdcard"; then
    echo "Error: SDXC card not mounted at /mnt/sdcard"
    echo "Please mount your SDXC card and try again"
    exit 1
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

# Make sure Python script is executable
chmod +x "$PYTHON_DIR/tracks-filler.py"

# Run the Python script
echo "Running tracks-filler.py to analyze library and generate copy script..."
python3 "$PYTHON_DIR/tracks-filler.py" "$TRACKS_FILE"

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
