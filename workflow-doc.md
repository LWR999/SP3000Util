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

4. Unmount the card:
   sudo umount ~/SP3000Util/mnt

5. Insert into your A&K SP3000 and enjoy!


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


SDXC CARD STRUCTURE
------------------

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
5. Unmount card

Scenario 3: Adding New Playlists to Existing Card
1. Mount card: ./process-playlists.sh /dev/sdc1
2. Add new Excel files to _playlists directory
3. Run: ./process-playlists.sh (no need to specify device again)
4. Unmount card


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

For any issues or questions, refer to the source code or consult your music server administrator.
