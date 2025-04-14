#!/usr/bin/env python3

"""
Playlist Processor for A&K SP3000
---------------------------------
This script:
1. Looks in the _playlists directory for Excel files
2. Processes each track in each playlist
3. Copies the entire album containing each track from NAS to SDXC
4. Builds M3U files that describe each playlist
"""

import os
import sys
import pandas as pd
import time
from pathlib import Path
import subprocess
import re

# Configuration
NAS_ROOT_CD = "/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 16-Bit CD"
NAS_ROOT_HIRES = "/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 24-Bit HiRes"
SDXC_MOUNT = "/mnt/sdcard"
SDXC_CD = f"{SDXC_MOUNT}/CD"
SDXC_HIRES = f"{SDXC_MOUNT}/Hires"
PLAYLIST_DIR = f"{SDXC_MOUNT}/Playlists"

def ensure_directories_exist():
    """Ensure required directories exist"""
    os.makedirs(SDXC_CD, exist_ok=True)
    os.makedirs(SDXC_HIRES, exist_ok=True)
    os.makedirs(PLAYLIST_DIR, exist_ok=True)

def sanitize_filename(name):
    """Remove problematic characters from filenames"""
    # Replace characters that might cause issues
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized

def process_playlist_file(playlist_file):
    """Process a single playlist Excel file and create an M3U playlist"""
    print(f"\nProcessing playlist: {os.path.basename(playlist_file)}")
    
    # Generate output playlist name from Excel filename
    playlist_name = os.path.splitext(os.path.basename(playlist_file))[0]
    playlist_name = sanitize_filename(playlist_name)
    output_m3u = os.path.join(PLAYLIST_DIR, f"{playlist_name}.m3u")
    
    # Check if Excel file exists
    if not os.path.exists(playlist_file):
        print(f"Error: Playlist file not found: {playlist_file}")
        return False
    
    try:
        # Load the Excel file
        playlist_df = pd.read_excel(playlist_file)
        print(f"Loaded playlist with {len(playlist_df)} tracks")
        
        # Find path column
        path_column = None
        for col in playlist_df.columns:
            col_lower = str(col).lower()
            if 'path' in col_lower or 'file' in col_lower or 'location' in col_lower:
                path_column = col
                print(f"Using column '{path_column}' for file paths")
                break
        
        if not path_column:
            print(f"Error: Could not find path column in {playlist_file}")
            print("Available columns:", playlist_df.columns.tolist())
            return False
        
        # Find title and artist columns if available
        title_column = None
        artist_column = None
        
        for col in playlist_df.columns:
            col_lower = str(col).lower()
            if 'title' in col_lower:
                title_column = col
            elif 'artist' in col_lower and 'album' not in col_lower:
                artist_column = col
        
        if title_column:
            print(f"Using column '{title_column}' for track titles")
        if artist_column:
            print(f"Using column '{artist_column}' for artists")
        
        # Prepare to create M3U file
        with open(output_m3u, 'w', encoding='utf-8') as m3u:
            # Write M3U header
            m3u.write("#EXTM3U\n")
            
            # Track stats
            processed_tracks = 0
            copied_albums = set()
            
            # Process each track
            for index, row in playlist_df.iterrows():
                # Get track path
                track_path = row.get(path_column)
                
                # Skip if path is missing
                if pd.isna(track_path) or not track_path:
                    print(f"  Warning: Missing path for track at row {index+2}")
                    continue
                
                track_path = str(track_path)
                
                # Get album directory
                album_path = os.path.dirname(track_path)
                
                # Skip if not in expected NAS paths
                if not (album_path.startswith(NAS_ROOT_CD) or album_path.startswith(NAS_ROOT_HIRES)):
                    print(f"  Warning: Track path not in expected NAS location: {track_path}")
                    continue
                
                # Get title and artist if available
                title = str(row.get(title_column, "")) if title_column and not pd.isna(row.get(title_column)) else os.path.basename(track_path)
                artist = str(row.get(artist_column, "")) if artist_column and not pd.isna(row.get(artist_column)) else ""
                
                # Map paths from NAS to SDXC
                if album_path.startswith(NAS_ROOT_CD):
                    rel_path = album_path[len(NAS_ROOT_CD):].lstrip('/')
                    sdxc_album_path = os.path.join(SDXC_CD, rel_path)
                    sdxc_track_path = os.path.join(SDXC_CD, track_path[len(NAS_ROOT_CD):].lstrip('/'))
                elif album_path.startswith(NAS_ROOT_HIRES):
                    rel_path = album_path[len(NAS_ROOT_HIRES):].lstrip('/')
                    sdxc_album_path = os.path.join(SDXC_HIRES, rel_path)
                    sdxc_track_path = os.path.join(SDXC_HIRES, track_path[len(NAS_ROOT_HIRES):].lstrip('/'))
                else:
                    print(f"  Error: Could not map path: {track_path}")
                    continue
                
                # Copy album if not already copied
                if album_path not in copied_albums:
                    # Create target directory
                    os.makedirs(os.path.dirname(sdxc_album_path), exist_ok=True)
                    
                    # Check if album already exists
                    if os.path.exists(sdxc_album_path) and os.listdir(sdxc_album_path):
                        print(f"  Album already exists: {sdxc_album_path}")
                    else:
                        print(f"  Copying album: {album_path}")
                        
                        # Escape special characters in paths
                        album_path_escaped = album_path.replace("'", "'\\''")
                        sdxc_album_path_escaped = sdxc_album_path.replace("'", "'\\''")
                        
                        # Build rsync command
                        cmd = f"rsync -rtv --progress --no-owner --no-group '{album_path_escaped}/' '{sdxc_album_path_escaped}/'"
                        
                        # Execute rsync
                        try:
                            subprocess.run(cmd, shell=True, check=True)
                            print(f"  Album copied successfully")
                        except subprocess.CalledProcessError as e:
                            print(f"  Error copying album: {e}")
                    
                    # Mark album as processed
                    copied_albums.add(album_path)
                
                # Add track to playlist
                m3u.write(f"#EXTINF:-1,{artist} - {title}\n")
                m3u.write(f"{sdxc_track_path}\n")
                
                processed_tracks += 1
                
                # Show progress
                if (index + 1) % 10 == 0:
                    print(f"  Processed {index + 1} tracks...")
        
        print(f"Created playlist: {output_m3u}")
        print(f"Processed {processed_tracks} tracks and copied {len(copied_albums)} albums")
        return True
    
    except Exception as e:
        print(f"Error processing playlist {playlist_file}: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_all_playlists(playlists_dir):
    """Process all Excel files in the playlists directory"""
    print(f"Processing all playlists in: {playlists_dir}")
    
    # Get all Excel files in the directory
    playlist_files = [os.path.join(playlists_dir, f) for f in os.listdir(playlists_dir) 
                     if f.lower().endswith('.xlsx') and os.path.isfile(os.path.join(playlists_dir, f))]
    
    if not playlist_files:
        print(f"No playlist Excel files found in {playlists_dir}")
        return 0
    
    print(f"Found {len(playlist_files)} playlist files")
    
    # Process each playlist file
    successful = 0
    for playlist_file in playlist_files:
        if process_playlist_file(playlist_file):
            successful += 1
    
    print(f"\nSuccessfully processed {successful} of {len(playlist_files)} playlists")
    return successful

def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python process-playlists.py <playlists_directory>")
        sys.exit(1)
    
    playlists_dir = sys.argv[1]
    
    # Check if playlists directory exists
    if not os.path.isdir(playlists_dir):
        print(f"Error: Playlists directory not found: {playlists_dir}")
        sys.exit(1)
    
    # Check if SDXC card is mounted
    if not os.path.ismount(SDXC_MOUNT):
        print(f"Error: SDXC card not mounted at {SDXC_MOUNT}")
        sys.exit(1)
    
    # Ensure required directories exist
    ensure_directories_exist()
    
    # Process all playlists
    process_all_playlists(playlists_dir)

if __name__ == "__main__":
    main()
