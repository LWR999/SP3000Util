SP3000 SDXC CARD PREPARATION WORKFLOW
====================================

QUICK START WORKFLOW
--------------------

For preparing a new SDXC card:

1. Mount your SDXC card at /mnt/sdcard:
   sudo mkdir -p /mnt/sdcard
   sudo mount /dev/sdX1 /mnt/sdcard

2. Process your playlists:
   ./process-playlists.sh
   (This copies all albums from your playlists and creates M3U files)

3. Fill remaining space (optional):
   ./fill-sdxc.sh
   ./fill_remaining_space.sh

4. Create additional genre playlists (optional):
   ./create-playlists.sh

5. Unmount card:
   sudo umount /mnt/sdcard

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


SCRIPT DETAILS
-------------

1. process-playlists.sh
   Purpose: Process all playlist Excel files, copy needed albums, and create M3U playlists.
   Usage: ./process-playlists.sh
   
   This script:
   - Looks in the _playlists directory for Excel files
   - For each Excel file, processes all tracks in the playlist
   - Copies the entire album for each track from NAS to SDXC
   - Creates an M3U file for each playlist Excel file
   - Places M3U files in /mnt/sdcard/Playlists/

2. fill-sdxc.sh
   Purpose: Analyze your library and prepare for filling your SDXC card with additional music.
   Usage: ./fill-sdxc.sh
   Output: fill_remaining_space.sh script
   
   This script:
   - Verifies your SDXC card is mounted
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
   Usage: ./create-playlists.sh
   
   This script:
   - Verifies your SDXC card is mounted and contains music
   - Calls playlist-generator.py in the _python directory
   - Creates genre-based playlists and a discovery playlist
   - Saves playlists to /mnt/sdcard/Playlists


PYTHON SCRIPTS (INSIDE _PYTHON DIRECTORY)
---------------------------------------

1. process-playlists.py
   Purpose: Core script for processing playlists and copying albums.
   Called by: process-playlists.sh
   
   This script:
   - Processes all Excel files in the _playlists directory
   - For each track, copies its entire album to the SDXC card
   - Creates M3U files with proper paths to the SDXC card

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


SDXC CARD STRUCTURE
------------------

The SDXC card will be organized as follows:

/mnt/sdcard/
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


TYPICAL USAGE SCENARIOS
---------------------

Scenario 1: Copy Just Your Playlist Albums
1. Mount SDXC card
2. Run ./process-playlists.sh
3. Unmount card

Scenario 2: Full Card with All Features
1. Mount SDXC card
2. Run ./process-playlists.sh
3. Run ./fill-sdxc.sh
4. Run ./fill_remaining_space.sh
5. Run ./create-playlists.sh
6. Unmount card

Scenario 3: Adding New Playlists to Existing Card
1. Mount SDXC card with existing content
2. Add new Excel files to _playlists directory
3. Run ./process-playlists.sh
4. Unmount card


TROUBLESHOOTING
--------------

Permission Errors:
- "Operation not permitted" errors during copying are warnings about ownership
- These can be safely ignored as long as the files show 100% completion

Path Issues:
- These scripts assume your library follows paths from your Roon database
- If paths don't match, check the detailed logging

Directory Structure:
- If you change the directory structure, make sure to update the paths in the wrapper scripts
- The default structure assumes _python/, _library/, and _playlists/ directories

Insufficient Space:
- If your card is too full, you may need to modify the scripts to target a smaller size

Multiple Sessions:
- If you need to stop and restart, just run the scripts again
- They're designed to skip files that are already copied


ADDITIONAL NOTES
--------------

- The process-playlists.sh script prioritizes your curated playlists
- The genre-based playlists follow a DJ-like flow: starting medium energy, building up, then cooling down
- The discovery playlist prioritizes tracks with low play counts
- You can re-run any script to refresh or update content
- Your original library files remain untouched during this process

For any issues or questions, refer to the source code comments or consult your music server administrator.
