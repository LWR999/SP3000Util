SP3000 SDXC CARD PREPARATION WORKFLOW
====================================

QUICK START WORKFLOW
--------------------

For preparing a new SDXC card:

1. Mount your SDXC card
   ./process-playlists.sh /dev/sdX1
   (Replace /dev/sdX1 with your actual SD card device)

2. Optionally fill remaining space:
   ./fill-sdxc.sh
   ./fill_remaining_space.sh

3. Optionally create genre playlists:
   ./create-playlists.sh

4. Optionally clean up clutter files:
   ./declutter.sh /dev/sdX1

5. Unmount the card:
   sudo umount ~/SP3000Util/mnt

6. Insert into your A&K SP3000 and enjoy!


DIRECTORY STRUCTURE
------------------

The utility has the following directory structure:

- _library/          : Contains library Excel files
  - LibraryAlbum.xlsx  : Album information
  - LibraryTracks.xlsx : Track information

- _playlists/        : Contains playlist Excel files
  - Various Soulpersona and other playlist files

- _python/           : Contains Python scripts
  - tracks-filler.py        : Script to analyze library and generate copy script
  - playlist-generator.py   : Script to create genre-based playlists
  - process-playlists.py    : Script to process playlist Excel files

- fill-sdxc.sh           : Wrapper script to analyze library and prepare copy script
- create-playlists.sh    : Wrapper script to create genre-based playlists
- process-playlists.sh   : Wrapper script to process playlist Excel files
- fill_remaining_space.sh : Generated script for copying files (created by fill-sdxc.sh)
- declutter.sh           : Script to clean up unwanted files from the SDXC card


SDXC CARD STRUCTURE
------------------

ALWAYS NAME THE SDXC CARD AS "MUSIC_SDXC"
The SDXC card will be organized as follows:

/Music/
|-- CD/            : 16-bit CD quality files
|   |-- Artist1/    
|   |   |-- Album1/
|   |   |   |-- 01 Track.flac
|   |   |   |-- 02 Track.flac
|   |   |   \-- ...
|   |   \-- ...
|   \-- ...
|
|-- Hires/         : 24-bit high-resolution files
|   |-- Artist1/
|   |   |-- Album1/
|   |   |   |-- 01 Track.flac
|   |   |   \-- ...
|   |   \-- ...
|   \-- ...
|
\-- Playlists/     : Generated M3U playlists
    |-- PlaylistName1.m3u   : Playlists from Excel files
    |-- PlaylistName2.m3u
    |-- ...
    |-- Electronic_Top50.m3u : Generated genre playlists
    |-- Jazz_Top50.m3u
    |-- Hip-Hop_Top50.m3u
    |-- Discovery_50.m3u
    \-- ...


SCRIPT DETAILS
-------------

1. process-playlists.sh
   Purpose: Process all playlist Excel files, copy needed albums, and create M3U playlists.
   Usage: ./process-playlists.sh [device]
   Example: ./process-playlists.sh /dev/sdc1
   
   This script:
   - Mounts the SD card if given a device parameter
   - Looks in the _playlists directory for Excel files
   - For each Excel file, processes all tracks in the playlist
   - Copies the entire album for each track from NAS to SDXC
   - Creates an M3U file for each playlist Excel file using relative paths
   - Places M3U files in /Music/Playlists/

2. fill-sdxc.sh
   Purpose: Analyze your library and prepare for filling your SDXC card with additional music.
   Usage: ./fill-sdxc.sh [device]
   Example: ./fill-sdxc.sh /dev/sdc1
   
   This script:
   - Mounts the SD card if given a device parameter
   - Calls tracks-filler.py in the _python directory
   - Generates a script (fill_remaining_space.sh) to copy additional albums

3. fill_remaining_space.sh
   Purpose: Copies additional albums to your SDXC card.
   Usage: ./fill_remaining_space.sh
   
   This script:
   - Created by fill-sdxc.sh
   - Uses rsync to safely copy files
   - Shows progress during copying
   - Organizes music into CD (16-bit) and HiRes (24-bit) directories

4. create-playlists.sh
   Purpose: Create smart genre-based playlists from music on your SDXC card.
   Usage: ./create-playlists.sh [device]
   Example: ./create-playlists.sh /dev/sdc1
   
   This script:
   - Mounts the SD card if given a device parameter
   - Calls playlist-generator.py in the _python directory
   - Creates genre-based playlists and a discovery playlist
   - Uses relative paths in playlist files
   - Saves playlists to /Music/Playlists/

5. declutter.sh
   Purpose: Clean up clutter files from an SDXC card.
   Usage: ./declutter.sh <device_partition>
   Example: ./declutter.sh /dev/sdc1
   
   This script:
   - Mounts the device if not already mounted
   - Removes the following clutter:
     * Artwork and artwork folders
     * Hidden files (starting with ".")
     * Files with specified extensions (jpg, txt, log, url, png)
     * Mac Finder metadata files (.DS_Store and others)
   - Reports the number of files deleted in each category
   - Safely unmounts the device when complete
   - Useful for cleaning up a card before adding music or after copying from other systems

6. snapshot-card.sh
   Purpose: Create a snapshot file of all album paths on an SDXC card.
   Usage: ./snapshot-card.sh <device_partition>
   Example: ./snapshot-card.sh /dev/sdc1
   
   This script:
   - Mounts the SD card if not already mounted
   - Scans the current card to identify all albums present
   - Creates a snapshot file (sd_snap_DATE_TIME.txt) with paths to all albums
   - Stores snapshots in the ~/SP3000Util/snapshots directory
   - Reports the number of CD and HiRes albums found

7. rebuild-sdxc.sh
   Purpose: Rebuild an SDXC card from a previously created snapshot file.
   Usage: ./rebuild-sdxc.sh <device_partition> <snapshot_file> [resume]
   Example: ./rebuild-sdxc.sh /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_20250422_120000.txt
   Example with resume: ./rebuild-sdxc.sh /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_20250422_120000.txt resume
   
   This script:
   - Mounts the SD card if not already mounted
   - Reads album paths from the snapshot file
   - Creates the basic directory structure (Music/CD, Music/Hires, Music/Playlists)
   - Erases existing content (unless in resume mode)
   - Copies all albums listed in the snapshot from server to SD card
   - Uses rsync for efficient copying with progress display
   - Excludes common clutter files during copying


Add these to TYPICAL USAGE SCENARIOS:

Scenario 5: Backing Up Your Optimal Card Setup
1. ./snapshot-card.sh /dev/sdc1
   (This creates a snapshot file of all albums on the card)

Scenario 6: Recreating Your Optimal Card Setup
1. ./rebuild-sdxc.sh /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_YYYYMMDD_HHMMSS.txt
2. ./create-playlists.sh
3. Unmount card

Scenario 7: Resuming a Failed Copy Operation
1. ./rebuild-sdxc.sh /dev/sdc1 ~/SP3000Util/snapshots/sd_snap_YYYYMMDD_HHMMSS.txt resume
2. ./create-playlists.sh (if needed)
3. Unmount card

PYTHON SCRIPTS (INSIDE _PYTHON DIRECTORY)
---------------------------------------

1. process-playlists.py
   Purpose: Core script for processing playlists and copying albums.
   Called by: process-playlists.sh
   
   This script:
   - Processes all Excel files in the _playlists directory
   - For each track, copies its entire album to the SDXC card
   - Creates M3U files with relative paths to the SDXC card

2. tracks-filler.py
   Purpose: Core script to analyze your library and prepare for copying additional albums.
   Called by: fill-sdxc.sh
   
   This script:
   - Reads your library data from Excel files
   - Determines which albums are not yet on your SDXC card
   - Optimizes selection to maximize variety within the 1TB limit
   - Generates the fill_remaining_space.sh script

3. playlist-generator.py
   Purpose: Core script to create intelligent genre-based playlists.
   Called by: create-playlists.sh
   
   This script:
   - Scans your SDXC card for music files
   - Analyzes file structure for artist/album/genre information
   - Creates DJ-like flow-optimized playlists for different genres
   - Builds a discovery playlist of tracks with low play counts
   - Uses relative paths in playlist files


TYPICAL USAGE SCENARIOS
---------------------

Scenario 1: Copy Just Your Playlist Albums
1. ./process-playlists.sh /dev/sdc1
2. Unmount card

Scenario 2: Full Card with All Features
1. ./process-playlists.sh /dev/sdc1
2. ./fill-sdxc.sh  (no need to specify device again if already mounted)
3. ./fill_remaining_space.sh
4. ./create-playlists.sh
5. ./declutter.sh  (to remove any unnecessary files)
6. Unmount card

Scenario 3: Adding New Playlists to Existing Card
1. Mount card: ./process-playlists.sh /dev/sdc1
2. Add new Excel files to _playlists directory
3. Run: ./process-playlists.sh (no need to specify device again)
4. Optionally run: ./declutter.sh (to clean up any clutter files)
5. Unmount card

Scenario 4: Cleaning Up a Messy Card
1. ./declutter.sh /dev/sdc1
2. Card will be unmounted when complete


MOUNTING DETAILS
--------------

The scripts use a mount point in your home directory to avoid needing sudo privileges:
- Default mount point: ~/SP3000Util/mnt
- The scripts will mount the card here if you provide a device parameter
- If already mounted elsewhere, specify the mount point as the second parameter

To allow mounting without sudo, you can either:
1. Configure /etc/fstab with the user option
2. Use udisksctl: udisksctl mount -b /dev/sdc1
3. Configure pmount for regular users


TROUBLESHOOTING
--------------

Permission Errors:
- "Operation not permitted" errors during copying are warnings about ownership
- These can be safely ignored as long as the files show 100% completion

Path Issues:
- These scripts assume your library follows the expected paths
- Make sure the NAS_ROOT_CD and NAS_ROOT_HIRES in the Python scripts match your setup

Directory Structure:
- If you change the directory structure, make sure to update the paths in all scripts

Mounting Issues:
- If you can't mount without sudo, use "udisksctl mount -b /dev/sdX1" first

Playlist Path Errors:
- If you see errors with "Soul/Funk", the updated scripts handle this by replacing slashes with dashes


ADDITIONAL NOTES
--------------

- The playlists use relative paths (../CD/ or ../Hires/) which will work correctly on the SP3000
- The genre-based playlists follow a DJ-like flow pattern
- The discovery playlist prioritizes tracks with low play counts
- You can re-run any script to update or refresh content
- Your original library files remain untouched during this process
- The declutter.sh script can be run any time to clean up unwanted files from your card

For any issues or questions, refer to the source code or consult your music server administrator.
