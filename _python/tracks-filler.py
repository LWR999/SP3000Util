#!/usr/bin/env python3

"""
Track-Based SDXC Space Filler
-----------------------------
This script uses the track-level data (which should contain paths)
instead of album-level data to fill the SDXC card.

Updated to better handle special characters in filenames.
Album limit removed to fill card to capacity.
"""

import os
import sys
import pandas as pd
import random
import time
from pathlib import Path
from collections import defaultdict

# Configuration
NAS_ROOT_CD = "/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 16-Bit CD"
NAS_ROOT_HIRES = "/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 24-Bit HiRes"
SDXC_MOUNT = "/mnt/sdcard"
SDXC_CD = f"{SDXC_MOUNT}/CD"
SDXC_HIRES = f"{SDXC_MOUNT}/Hires"
MAX_SIZE = 1000000000000  # 1TB in bytes

def get_sdxc_usage():
    """Calculate current SDXC card usage"""
    try:
        total_size = 0
        # Walk through CD directory
        if os.path.exists(SDXC_CD):
            for dirpath, dirnames, filenames in os.walk(SDXC_CD):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        
        # Walk through HiRes directory
        if os.path.exists(SDXC_HIRES):
            for dirpath, dirnames, filenames in os.walk(SDXC_HIRES):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        
        return total_size
    except Exception as e:
        print(f"Error calculating SDXC usage: {e}")
        return 0

def get_copied_albums():
    """Get list of albums already on the SDXC card"""
    copied_albums = set()
    
    # Check CD directory
    if os.path.exists(SDXC_CD):
        for root, dirs, files in os.walk(SDXC_CD):
            # If it has music files, consider it an album directory
            has_music = False
            for f in files:
                if f.lower().endswith(('.flac', '.mp3', '.wav', '.aiff', '.alac', '.dsf', '.dff')):
                    has_music = True
                    break
            
            if has_music:
                rel_path = os.path.relpath(root, SDXC_CD)
                nas_path = os.path.join(NAS_ROOT_CD, rel_path)
                copied_albums.add(nas_path)
    
    # Check HiRes directory
    if os.path.exists(SDXC_HIRES):
        for root, dirs, files in os.walk(SDXC_HIRES):
            # If it has music files, consider it an album directory
            has_music = False
            for f in files:
                if f.lower().endswith(('.flac', '.mp3', '.wav', '.aiff', '.alac', '.dsf', '.dff')):
                    has_music = True
                    break
            
            if has_music:
                rel_path = os.path.relpath(root, SDXC_HIRES)
                nas_path = os.path.join(NAS_ROOT_HIRES, rel_path)
                copied_albums.add(nas_path)
    
    print(f"Found {len(copied_albums)} albums already on SDXC card")
    print("Sample of copied albums:")
    for album in list(copied_albums)[:5]:
        print(f"  - {album}")
    
    return copied_albums

def get_albums_from_tracks(track_file):
    """Extract albums from the tracks Excel file"""
    all_albums = {}
    
    try:
        # Load from tracks file
        print(f"Loading track data from: {track_file}")
        tracks_df = pd.read_excel(track_file)
        print(f"Loaded {len(tracks_df)} tracks")
        
        # Debug: Show column names
        print("Excel columns:", tracks_df.columns.tolist())
        
        # Check for path column
        path_column = None
        for col in tracks_df.columns:
            if 'path' in str(col).lower() or 'file' in str(col).lower() or 'location' in str(col).lower():
                path_column = col
                print(f"Found path column: '{path_column}'")
                break
        
        if not path_column:
            print("WARNING: No path column found in track data!")
            # Try to find something that looks like a path
            for col in tracks_df.columns:
                sample = tracks_df[col].iloc[0] if not tracks_df.empty else None
                if isinstance(sample, str) and ('/' in sample or '\\' in sample):
                    path_column = col
                    print(f"Using column '{path_column}' as path column")
                    break
        
        if not path_column:
            print("ERROR: Cannot find path column in track data!")
            # Show all string columns as possible candidates
            for col in tracks_df.columns:
                sample = tracks_df[col].iloc[0] if not tracks_df.empty else None
                if isinstance(sample, str):
                    print(f"  String column: '{col}' - Sample: '{sample}'")
            return {}
        
        # Group tracks by album
        album_tracks = defaultdict(list)
        album_info = {}
        
        track_count = 0
        no_path_count = 0
        wrong_path_count = 0
        
        for i, track in tracks_df.iterrows():
            path = track.get(path_column, '')
            
            # Debug every 1000 rows
            if i % 1000 == 0 and i > 0:
                print(f"Processing row {i}, found {len(album_tracks)} albums so far")
            
            if pd.isna(path) or not path:
                no_path_count += 1
                if no_path_count <= 5:
                    print(f"Row {i} has no path")
                continue
            
            # Debug path format
            if i < 5:
                print(f"Row {i} path: '{path}'")
            
            # Extract album path (parent directory)
            album_path = os.path.dirname(path)
            
            # Check path format
            if not (album_path.startswith(NAS_ROOT_CD) or album_path.startswith(NAS_ROOT_HIRES)):
                wrong_path_count += 1
                if wrong_path_count <= 5:
                    print(f"Row {i} has wrong album path format: '{album_path}'")
                continue
            
            # Add track to album
            album_tracks[album_path].append(path)
            
            # Update album info
            if album_path not in album_info:
                album_info[album_path] = {
                    'path': album_path,
                    'artist': track.get('Artist', ''),
                    'album': track.get('Album', ''),
                    'album_artist': track.get('AlbumArtist', ''),
                    'genre': track.get('Genre', ''),
                    'size': 0,
                    'play_count': 0
                }
            
            # Update size
            size = track.get('Size', 0)
            if not pd.isna(size) and size > 0:
                album_info[album_path]['size'] += size
            
            # Update play count
            play_count = track.get('PlayCount', 0)
            if not pd.isna(play_count) and play_count > 0:
                album_info[album_path]['play_count'] += play_count
            
            track_count += 1
        
        # Create final album list
        for album_path, tracks in album_tracks.items():
            all_albums[album_path] = album_info[album_path]
            
            # If album has no size yet, try to get it from file system
            if all_albums[album_path]['size'] == 0:
                try:
                    total_size = 0
                    for track_path in tracks:
                        if os.path.exists(track_path):
                            total_size += os.path.getsize(track_path)
                    all_albums[album_path]['size'] = total_size
                except Exception as e:
                    print(f"Error getting size for {album_path}: {e}")
        
        print(f"Processed {track_count} tracks into {len(all_albums)} albums")
        print(f"Skipped {no_path_count} tracks with no path")
        print(f"Skipped {wrong_path_count} tracks with wrong path format")
        
        # Debug: Show sample of found albums
        print("Sample of found albums:")
        for path, album in list(all_albums.items())[:5]:
            print(f"  - {path} ({album['artist']} - {album['album']}), Size: {album['size']:,} bytes")
    
    except Exception as e:
        print(f"Error processing track file: {e}")
        import traceback
        traceback.print_exc()
    
    return all_albums

def generate_copy_script(albums_to_copy, remaining_space):
    """Generate a script to copy albums to fill remaining space"""
    if not albums_to_copy:
        print("No albums to copy!")
        script_path = "fill_remaining_space.sh"
        with open(script_path, 'w') as script:
            script.write("#!/bin/bash\n\n")
            script.write("# No albums found to copy\n")
            script.write("echo \"No albums found to copy!\"\n")
        os.chmod(script_path, 0o755)
        return 0, 0
    
    script_path = "fill_remaining_space.sh"
    
    with open(script_path, 'w') as script:
        script.write("#!/bin/bash\n\n")
        script.write("# Script to fill remaining SDXC space with albums\n")
        script.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Add progress tracking
        script.write("# Track progress\n")
        script.write("TOTAL_ALBUMS=%d\n" % len(albums_to_copy))
        script.write("CURRENT_ALBUM=0\n\n")
        
        # Add rsync commands
        total_size = 0
        album_count = 0
        
        for album in albums_to_copy:
            # Skip if adding this album would exceed space
            if total_size + album['size'] > remaining_space:
                continue
            
            path = album['path']
            
            # Determine target path
            if path.startswith(NAS_ROOT_HIRES):
                relative_path = path[len(NAS_ROOT_HIRES):].lstrip('/')
                target_path = os.path.join(SDXC_HIRES, relative_path)
            else:
                relative_path = path[len(NAS_ROOT_CD):].lstrip('/')
                target_path = os.path.join(SDXC_CD, relative_path)
            
            # Add copy command
            artist = album['artist'] or album['album_artist'] or "Unknown Artist"
            album_name = album['album'] or os.path.basename(path)
            
            # Escape special characters in paths by using single quotes
            # But we need to handle any single quotes in the paths themselves
            path_escaped = path.replace("'", "'\\''")
            target_path_escaped = target_path.replace("'", "'\\''")
            
            # Increment counter and show progress
            script.write("CURRENT_ALBUM=$((CURRENT_ALBUM + 1))\n")
            script.write(f"echo \"Copying album $CURRENT_ALBUM of $TOTAL_ALBUMS: {artist.replace('"', '\\"')} - {album_name.replace('"', '\\"')}\"\n")
            
            script.write(f"mkdir -p '{os.path.dirname(target_path_escaped)}'\n")
            script.write(f"rsync -rtv --progress --no-owner --no-group '{path_escaped}/' '{target_path_escaped}/'\n\n")
            
            # Add a checkpoint every 20 albums
            if album_count % 20 == 0 and album_count > 0:
                script.write(f"echo \"Copied {album_count} albums so far...\"\n\n")
            
            total_size += album['size']
            album_count += 1
            
            # No album limit - include all albums that fit
        
        # Add summary
        script.write(f"echo \"Copied {album_count} albums using approximately {total_size / (1024*1024*1024):.2f} GB\"\n")
        script.write("echo \"Space filling complete!\"\n")
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    print(f"Generated script to copy {album_count} albums using {total_size / (1024*1024*1024):.2f} GB")
    print(f"Script saved to: {script_path}")
    
    return album_count, total_size

def main():
    if len(sys.argv) < 2:
        print("Usage: python tracks-filler.py <tracks_excel> [<album_excel>]")
        sys.exit(1)
    
    track_file = sys.argv[1]
    
    # Step 1: Get current SDXC usage
    current_usage = get_sdxc_usage()
    remaining_space = MAX_SIZE - current_usage
    print(f"Current SDXC usage: {current_usage / (1024*1024*1024):.2f} GB")
    print(f"Remaining space: {remaining_space / (1024*1024*1024):.2f} GB")
    
    if remaining_space <= 0:
        print("No space remaining on SDXC card!")
        sys.exit(0)
    
    # Step 2: Get already copied albums
    copied_albums = get_copied_albums()
    
    # Step 3: Get all albums from track data
    all_albums = get_albums_from_tracks(track_file)
    
    # Step 4: Filter out already copied albums
    available_albums = []
    for path, album in all_albums.items():
        if path not in copied_albums and album['size'] > 0:
            available_albums.append(album)
    
    print(f"Found {len(available_albums)} albums available to copy")
    
    if not available_albums:
        print("No albums available to copy! Debugging info:")
        print(f"Total albums in library: {len(all_albums)}")
        print(f"Already copied albums: {len(copied_albums)}")
        print("Possible issues:")
        print("1. Path formats don't match between library and copied albums")
        print("2. All albums already copied")
        print("3. No valid size information for albums")
        
        # Check for path format mismatches
        if all_albums and copied_albums:
            lib_sample = next(iter(all_albums.keys()))
            copy_sample = next(iter(copied_albums))
            print(f"Library path format: '{lib_sample}'")
            print(f"Copied path format: '{copy_sample}'")
        
        generate_copy_script([], remaining_space)
        sys.exit(0)
    
    # Step 5: Sort albums by criteria (size and play count)
    # First prioritize smaller albums to maximize variety
    available_albums.sort(key=lambda x: x['size'])
    
    # Take 75% smaller albums, 25% based on play count
    split_point = int(len(available_albums) * 0.75)
    smaller_albums = available_albums[:split_point]
    popular_albums = sorted(available_albums[split_point:], key=lambda x: x['play_count'], reverse=True)
    
    # Combine and shuffle within groups for variety
    random.shuffle(smaller_albums)
    prioritized_albums = smaller_albums + popular_albums
    
    # Step 6: Generate copy script
    album_count, total_size = generate_copy_script(prioritized_albums, remaining_space)
    
    if album_count > 0:
        print("\nTo fill the remaining space, run:")
        print("./fill_remaining_space.sh")
    else:
        print("\nNo additional albums could be added within the space constraints")

if __name__ == "__main__":
    main()
