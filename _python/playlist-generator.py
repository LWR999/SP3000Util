#!/usr/bin/env python3

"""
SDXC Card Playlist Generator
----------------------------
This script creates DJ-like flow-optimized playlists and a discovery playlist
from the music already on your SDXC card.

Updated to use the new directory structure and relative paths.
"""

import os
import sys
import pandas as pd
import random
import re
import time
from collections import defaultdict
from pathlib import Path

# Configuration
NAS_ROOT_CD = "/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 16-Bit CD"
NAS_ROOT_HIRES = "/home/music/drobos/hibiki/Media/Music/Lossless/FLAC 24-Bit HiRes"
TRACK_COUNT = 50  # Tracks per playlist

# Genre mapping to consolidate similar genres
GENRE_MAPPING = {
    # Electronic genres
    "electronic": "Electronic",
    "electronica": "Electronic",
    "electro": "Electronic",
    "synth": "Electronic",
    "techno": "Electronic",
    "idm": "Electronic",
    "ambient": "Electronic",
    "trip-hop": "Electronic",
    "trip hop": "Electronic",
    "downtempo": "Electronic",
    "lounge": "Electronic",
    "chillout": "Electronic",
    "experimental": "Electronic",
    "drum and bass": "Electronic",
    "drum & bass": "Electronic",
    "breakbeat": "Electronic",
    "industrial": "Electronic",
    
    # House genres
    "house": "House",
    "deep house": "House",
    "tech house": "House",
    "progressive house": "House",
    "acid house": "House",
    "disco house": "House",
    "funky house": "House",
    "soulful house": "House",
    "vocal house": "House",
    "garage": "House",
    
    # Hip-Hop genres
    "hip-hop": "Hip-Hop",
    "hip hop": "Hip-Hop",
    "rap": "Hip-Hop",
    "trap": "Hip-Hop",
    "r&b": "Hip-Hop",
    "rnb": "Hip-Hop",
    "rhythm and blues": "Hip-Hop",
    "urban": "Hip-Hop",
    
    # Jazz genres
    "jazz": "Jazz",
    "jazz fusion": "Jazz",
    "fusion": "Jazz",
    "jazz funk": "Jazz",
    "smooth jazz": "Jazz",
    "bebop": "Jazz",
    "big band": "Jazz",
    "bossa nova": "Jazz",
    "latin jazz": "Jazz",
    "acid jazz": "Jazz",
    "contemporary jazz": "Jazz",
    "swing": "Jazz",
    "free jazz": "Jazz",
    "modal jazz": "Jazz",
    "cool jazz": "Jazz",
    
    # Soul/Funk
    "soul": "Soul-Funk",
    "funk": "Soul-Funk",
    "neo-soul": "Soul-Funk",
    "neo soul": "Soul-Funk",
    "disco": "Soul-Funk",
    "motown": "Soul-Funk",
    "r&b": "Soul-Funk",
    "rhythm and blues": "Soul-Funk",
    
    # Rock
    "rock": "Rock",
    "indie": "Rock",
    "alternative": "Rock",
    "punk": "Rock",
    "post-punk": "Rock",
    "post-rock": "Rock",
    "psychedelic": "Rock",
    "progressive rock": "Rock",
    "classic rock": "Rock",
    "hard rock": "Rock",
    "metal": "Rock",
    
    # Classical
    "classical": "Classical",
    "orchestra": "Classical",
    "chamber": "Classical",
    "opera": "Classical",
    "piano": "Classical",
    "symphony": "Classical",
    "concerto": "Classical",
    "sonata": "Classical",
    
    # Miscellaneous
    "world": "World",
    "reggae": "Reggae-Dub",
    "dub": "Reggae-Dub",
    "folk": "Folk",
    "country": "Country",
    "blues": "Blues",
    "soundtrack": "Soundtrack",
    "pop": "Pop",
    "vocal": "Vocal",
    "new age": "New Age",
    "acoustic": "Acoustic"
}

# Globals
sdxc_tracks = []
genre_tracks = defaultdict(list)
track_info = {}
play_count_data = {}

def scan_sdxc_for_tracks(mount_dir):
    """Scan the SDXC card for music files and build a track database"""
    global sdxc_tracks, genre_tracks
    
    # New directory structure
    sdxc_cd = os.path.join(mount_dir, "Music", "CD")
    sdxc_hires = os.path.join(mount_dir, "Music", "Hires")
    playlist_dir = os.path.join(mount_dir, "Music", "Playlists")
    
    print("Scanning SDXC card for music files...")
    
    music_extensions = ('.flac', '.mp3', '.wav', '.aiff', '.alac', '.ape', '.dsf', '.dff')
    
    # Scan CD directory
    if os.path.exists(sdxc_cd):
        for root, dirs, files in os.walk(sdxc_cd):
            for file in files:
                if file.lower().endswith(music_extensions):
                    track_path = os.path.join(root, file)
                    sdxc_tracks.append(track_path)
    
    # Scan HiRes directory
    if os.path.exists(sdxc_hires):
        for root, dirs, files in os.walk(sdxc_hires):
            for file in files:
                if file.lower().endswith(music_extensions):
                    track_path = os.path.join(root, file)
                    sdxc_tracks.append(track_path)
    
    print(f"Found {len(sdxc_tracks)} music tracks on SDXC card")
    
    # Create playlist directory if it doesn't exist
    os.makedirs(playlist_dir, exist_ok=True)
    
    return sdxc_cd, sdxc_hires, playlist_dir

def extract_track_info_from_paths(sdxc_cd, sdxc_hires):
    """Extract track information from file paths and names"""
    global sdxc_tracks, track_info, genre_tracks
    
    print("Extracting track information from file paths...")
    
    def guess_genre_from_path(path):
        """Attempt to guess genre from the path"""
        path_lower = path.lower()
        for genre_keyword, mapped_genre in GENRE_MAPPING.items():
            if genre_keyword in path_lower:
                return mapped_genre
        return "Unknown"
    
    def extract_track_number(filename):
        """Extract track number from filename"""
        # Common patterns: 01 - Track.flac, 1. Track.flac, Track 01.flac
        patterns = [
            r'^(\d{1,2})[\s.\-_]+',  # 01 - Track, 01. Track, 01_Track
            r'[\s_-](\d{1,2})[\s.\-_]',  # Track 01 -, Track-01-
            r'Track\s*(\d{1,2})',  # Track01, Track 01
            r'[^\d](\d{1,2})[^\d]*$'  # Anything ending with a number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        return 0
    
    for track_path in sdxc_tracks:
        # Get file name and extract basic info
        filename = os.path.basename(track_path)
        directory = os.path.dirname(track_path)
        parent_dir = os.path.basename(directory)
        
        # Determine if track is in CD or HiRes
        is_hires = False
        is_cd = False
        
        # Get path relative to SDXC root - check for new structure
        if track_path.startswith(sdxc_hires):
            is_hires = True
            relative_path = os.path.relpath(track_path, sdxc_hires)
        elif track_path.startswith(sdxc_cd):
            is_cd = True
            relative_path = os.path.relpath(track_path, sdxc_cd)
        else:
            # Skip tracks outside of expected directories
            continue
        
        # Split path components for artist/album guessing
        path_parts = relative_path.split(os.path.sep)
        
        # Try to extract artist and album from path
        artist = path_parts[0] if len(path_parts) > 0 else "Unknown Artist"
        album = path_parts[1] if len(path_parts) > 1 else parent_dir
        
        # Clean up filename to get track title
        title = filename
        for ext in ('.flac', '.mp3', '.wav', '.aiff', '.alac', '.ape', '.dsf', '.dff'):
            title = title.replace(ext, '')
        
        # Remove track numbers from title
        title_clean = re.sub(r'^\d+[\s.\-_]+', '', title)
        
        # Extract track number
        track_number = extract_track_number(filename)
        
        # Guess genre from path
        genre = guess_genre_from_path(track_path)
        
        # Store track info
        track_info[track_path] = {
            'path': track_path,
            'artist': artist,
            'album': album,
            'title': title_clean or title,
            'track_number': track_number,
            'genre': genre,
            'is_hires': is_hires,
            'is_cd': is_cd
        }
        
        # Add to genre tracks
        genre_tracks[genre].append(track_path)
    
    # Also add tracks to broader genre groups
    major_genres = set(GENRE_MAPPING.values())
    for genre in list(major_genres):
        if genre not in genre_tracks:
            genre_tracks[genre] = []
            for track, info in track_info.items():
                if info['genre'] in genre or genre in info['genre']:
                    genre_tracks[genre].append(track)

def load_play_count_data(tracks_excel):
    """Load play count data from the tracks Excel file if available"""
    global play_count_data
    
    if not tracks_excel or not os.path.exists(tracks_excel):
        print("No tracks Excel file provided. Skipping play count data.")
        return
    
    print(f"Loading play count data from: {tracks_excel}")
    
    try:
        tracks_df = pd.read_excel(tracks_excel)
        print(f"Loaded {len(tracks_df)} tracks from Excel")
        
        # Check for path and play count columns
        path_column = None
        play_count_column = None
        
        for col in tracks_df.columns:
            col_lower = str(col).lower()
            if 'path' in col_lower or 'file' in col_lower or 'location' in col_lower:
                path_column = col
            elif 'play' in col_lower and 'count' in col_lower:
                play_count_column = col
        
        if not path_column:
            print("Could not find path column in Excel. Using filenames for matching.")
            return
        
        if not play_count_column:
            print("Could not find play count column in Excel. All tracks will have equal play count.")
            return
        
        # Build play count mapping
        for _, row in tracks_df.iterrows():
            path = str(row.get(path_column, ''))
            play_count = row.get(play_count_column, 0)
            
            if pd.isna(path) or pd.isna(play_count):
                continue
            
            # Store by full path
            play_count_data[path] = play_count
            
            # Also store by filename for fallback matching
            filename = os.path.basename(path)
            if filename:
                play_count_data[filename] = play_count
        
        print(f"Loaded play count data for {len(play_count_data)} tracks")
    
    except Exception as e:
        print(f"Error loading play count data: {e}")
        import traceback
        traceback.print_exc()

def get_track_play_count(track_path):
    """Get play count for a track, with fallback matching"""
    # Try direct path match
    if track_path in play_count_data:
        return play_count_data[track_path]
    
    # Try matching by filename
    filename = os.path.basename(track_path)
    if filename in play_count_data:
        return play_count_data[filename]
    
    # Last resort: try fuzzy matching with any path ending
    for path, count in play_count_data.items():
        if path.endswith(filename) or filename.endswith(os.path.basename(path)):
            return count
    
    return 0  # Default to 0 if no match found

def create_flow_optimized_playlist(genre, count, playlist_dir, sdxc_cd, sdxc_hires):
    """Create a DJ-like flow-optimized playlist for a genre"""
    print(f"Creating flow-optimized playlist for {genre} ({count} tracks)...")
    
    # Get tracks for this genre
    genre_specific_tracks = genre_tracks.get(genre, [])
    
    if len(genre_specific_tracks) < 10:
        print(f"Not enough tracks for genre {genre}, looking for similar genres")
        # Look for similar genres
        for g, tracks in genre_tracks.items():
            if genre.lower() in g.lower() or g.lower() in genre.lower():
                genre_specific_tracks.extend(tracks)
    
    if len(genre_specific_tracks) < count:
        print(f"Still only found {len(genre_specific_tracks)} tracks for genre {genre}")
        if len(genre_specific_tracks) < 5:
            print(f"Too few tracks to create a playlist for {genre}")
            return False
    
    # Remove duplicates
    genre_specific_tracks = list(set(genre_specific_tracks))
    
    # Get info for all tracks
    track_entries = []
    for track_path in genre_specific_tracks:
        if track_path in track_info:
            info = track_info[track_path]
            
            # Calculate energy level (approximated by track number position in album)
            album_tracks = [t for t in genre_specific_tracks if track_info[t]['album'] == info['album']]
            track_count = len(album_tracks)
            track_number = info['track_number']
            
            # Approximate energy level
            if track_count > 0 and track_number > 0:
                # Position 0-1 within album (0 = first track, 1 = last track)
                position = (track_number - 1) / max(1, track_count - 1) if track_count > 1 else 0.5
                
                # Energy often follows a curve: starts medium, rises, then falls
                # Highest energy is often around 60-70% through the album
                # This creates a curve peaking at 0.65
                energy = 1 - abs(position - 0.65) * 1.5
                energy = max(0.1, min(1.0, energy))  # Keep between 0.1 and 1.0
            else:
                energy = 0.5  # Middle energy if we can't determine position
            
            # Get play count
            play_count = get_track_play_count(track_path)
            
            track_entries.append({
                'path': track_path,
                'artist': info['artist'],
                'title': info['title'],
                'album': info['album'],
                'track_number': track_number,
                'energy': energy,
                'play_count': play_count,
                'is_hires': info['is_hires'],
                'is_cd': info['is_cd']
            })
    
    # Limit to top tracks by play count if we have too many
    if len(track_entries) > count * 3:
        track_entries.sort(key=lambda x: x['play_count'], reverse=True)
        track_entries = track_entries[:count * 3]
    
    # Create DJ-like flow
    # 1. Start with medium energy
    # 2. Build up to high energy
    # 3. Maintain high energy
    # 4. Gradually bring energy down
    
    # Sort tracks by energy to allow us to select from different energy levels
    track_entries.sort(key=lambda x: x['energy'])
    
    # Select tracks for different parts of the mix
    total_tracks = min(count, len(track_entries))
    
    # Calculate how many tracks for each section
    intro_count = max(1, int(total_tracks * 0.15))  # 15% - Medium energy intro
    buildup_count = max(1, int(total_tracks * 0.30))  # 30% - Building energy
    peak_count = max(1, int(total_tracks * 0.30))  # 30% - High energy section
    outro_count = total_tracks - intro_count - buildup_count - peak_count  # Remaining - Cooldown
    
    # Energy ranges for each section
    intro_range = (0.3, 0.5)  # Medium energy
    buildup_range = (0.5, 0.8)  # Medium to high
    peak_range = (0.8, 1.0)  # Highest energy
    outro_range = (0.2, 0.5)  # Medium to low
    
    # Filter tracks for each section
    def filter_energy_range(tracks, min_e, max_e):
        return [t for t in tracks if min_e <= t['energy'] <= max_e]
    
    intro_tracks = filter_energy_range(track_entries, *intro_range)
    buildup_tracks = filter_energy_range(track_entries, *buildup_range)
    peak_tracks = filter_energy_range(track_entries, *peak_range)
    outro_tracks = filter_energy_range(track_entries, *outro_range)
    
    # If we don't have enough tracks in a specific energy range, take from the closest section
    if len(intro_tracks) < intro_count:
        # Get more tracks from the general pool and sort by distance to intro energy
        additional = [t for t in track_entries if t not in intro_tracks]
        additional.sort(key=lambda x: abs(x['energy'] - 0.4))  # Sort by closeness to middle of intro range
        intro_tracks.extend(additional[:intro_count - len(intro_tracks)])
    
    if len(buildup_tracks) < buildup_count:
        additional = [t for t in track_entries if t not in buildup_tracks and t not in intro_tracks]
        additional.sort(key=lambda x: abs(x['energy'] - 0.65))  # Middle of buildup range
        buildup_tracks.extend(additional[:buildup_count - len(buildup_tracks)])
    
    if len(peak_tracks) < peak_count:
        additional = [t for t in track_entries if t not in peak_tracks and t not in intro_tracks and t not in buildup_tracks]
        additional.sort(key=lambda x: abs(x['energy'] - 0.9))  # Middle of peak range
        peak_tracks.extend(additional[:peak_count - len(peak_tracks)])
    
    if len(outro_tracks) < outro_count:
        additional = [t for t in track_entries if t not in outro_tracks and t not in intro_tracks 
                     and t not in buildup_tracks and t not in peak_tracks]
        additional.sort(key=lambda x: abs(x['energy'] - 0.35))  # Middle of outro range
        outro_tracks.extend(additional[:outro_count - len(outro_tracks)])
    
    # Sort each section by energy (ascending for intro & buildup, descending for outro)
    intro_tracks.sort(key=lambda x: x['energy'])
    buildup_tracks.sort(key=lambda x: x['energy'])
    peak_tracks.sort(key=lambda x: random.random())  # Shuffle peak tracks for variety
    outro_tracks.sort(key=lambda x: -x['energy'])  # Descending energy
    
    # Select the number of tracks we need from each section
    selected_intro = intro_tracks[:intro_count]
    selected_buildup = buildup_tracks[:buildup_count]
    selected_peak = peak_tracks[:peak_count]
    selected_outro = outro_tracks[:outro_count]
    
    # Combine all sections for the final playlist
    final_tracks = selected_intro + selected_buildup + selected_peak + selected_outro
    
    # Ensure no duplicate tracks (can happen if sections overlap)
    seen_paths = set()
    unique_tracks = []
    for track in final_tracks:
        if track['path'] not in seen_paths:
            seen_paths.add(track['path'])
            unique_tracks.append(track)
    
    final_tracks = unique_tracks[:count]  # Limit to requested count
    
    # Create M3U playlist
    # Replace any slashes in genre name with dashes to avoid directory issues
    safe_genre = genre.replace('/', '-')
    playlist_name = f"{safe_genre}_Top{len(final_tracks)}"
    playlist_path = os.path.join(playlist_dir, f"{playlist_name}.m3u")
    
    with open(playlist_path, 'w', encoding='utf-8') as m3u:
        # Write M3U header
        m3u.write("#EXTM3U\n")
        
        # Write tracks with relative paths
        for track in final_tracks:
            track_path = track['path']
            
            # Convert absolute path to relative path from playlist directory
            if track['is_hires']:
                # For HiRes tracks: ../Hires/Artist/Album/track.flac
                rel_path = os.path.relpath(track_path, sdxc_hires)
                rel_track_path = os.path.join("../Hires", rel_path)
            else:
                # For CD tracks: ../CD/Artist/Album/track.flac
                rel_path = os.path.relpath(track_path, sdxc_cd)
                rel_track_path = os.path.join("../CD", rel_path)
            
            # Add track to playlist with metadata
            m3u.write(f"#EXTINF:-1,{track['artist']} - {track['title']}\n")
            m3u.write(f"{rel_track_path}\n")
    
    print(f"Created {genre} playlist with {len(final_tracks)} tracks: {playlist_path}")
    return True

def create_discovery_playlist(count, playlist_dir, sdxc_cd, sdxc_hires):
    """Create a discovery playlist of tracks with low or no play counts"""
    print(f"Creating discovery playlist with {count} tracks...")
    
    # Sort all tracks by play count (lowest first)
    discovery_candidates = []
    for track_path in sdxc_tracks:
        if track_path in track_info:
            info = track_info[track_path]
            play_count = get_track_play_count(track_path)
            
            discovery_candidates.append({
                'path': track_path,
                'artist': info['artist'],
                'title': info['title'],
                'album': info['album'],
                'genre': info['genre'],
                'play_count': play_count,
                'is_hires': info['is_hires'],
                'is_cd': info['is_cd']
            })
    
    # Sort by play count (lowest first)
    discovery_candidates.sort(key=lambda x: x['play_count'])
    
    # Create a diverse selection (different artists, albums, genres)
    selected_tracks = []
    artists_used = set()
    albums_used = set()
    genres_used = set()
    
    # First, get tracks with zero plays
    zero_play_tracks = [t for t in discovery_candidates if t['play_count'] == 0]
    
    # Shuffle zero play tracks for randomness
    random.shuffle(zero_play_tracks)
    
    # Take tracks ensuring diversity
    for track in zero_play_tracks:
        # Skip if we already have enough tracks
        if len(selected_tracks) >= count:
            break
        
        # Skip if we already have too many from this artist
        if track['artist'] in artists_used and len([t for t in selected_tracks if t['artist'] == track['artist']]) >= 3:
            continue
        
        # Skip if we already have too many from this album
        if track['album'] in albums_used and len([t for t in selected_tracks if t['album'] == track['album']]) >= 2:
            continue
        
        # Skip if we already have too many from this genre
        if track['genre'] in genres_used and len([t for t in selected_tracks if t['genre'] == track['genre']]) >= count / 4:
            continue
        
        # Add track
        selected_tracks.append(track)
        artists_used.add(track['artist'])
        albums_used.add(track['album'])
        genres_used.add(track['genre'])
    
    # If we still don't have enough tracks, add more from low play counts
    if len(selected_tracks) < count:
        low_play_tracks = [t for t in discovery_candidates if t not in selected_tracks]
        
        for track in low_play_tracks:
            if len(selected_tracks) >= count:
                break
            
            # Skip if we already have too many from this artist
            if track['artist'] in artists_used and len([t for t in selected_tracks if t['artist'] == track['artist']]) >= 3:
                continue
            
            # Skip if we already have too many from this album
            if track['album'] in albums_used and len([t for t in selected_tracks if t['album'] == track['album']]) >= 2:
                continue
            
            # Add track
            selected_tracks.append(track)
            artists_used.add(track['artist'])
            albums_used.add(track['album'])
    
    # Shuffle for final order
    random.shuffle(selected_tracks)
    selected_tracks = selected_tracks[:count]
    
    # Create M3U playlist
    playlist_path = os.path.join(playlist_dir, "Discovery_50.m3u")
    
    with open(playlist_path, 'w', encoding='utf-8') as m3u:
        # Write M3U header
        m3u.write("#EXTM3U\n")
        
        # Write tracks with relative paths
        for track in selected_tracks:
            track_path = track['path']
            
            # Convert absolute path to relative path from playlist directory
            if track['is_hires']:
                # For HiRes tracks: ../Hires/Artist/Album/track.flac
                rel_path = os.path.relpath(track_path, sdxc_hires)
                rel_track_path = os.path.join("../Hires", rel_path)
            else:
                # For CD tracks: ../CD/Artist/Album/track.flac
                rel_path = os.path.relpath(track_path, sdxc_cd)
                rel_track_path = os.path.join("../CD", rel_path)
            
            # Add track to playlist with metadata
            m3u.write(f"#EXTINF:-1,{track['artist']} - {track['title']}\n")
            m3u.write(f"{rel_track_path}\n")
    
    print(f"Created discovery playlist with {len(selected_tracks)} tracks: {playlist_path}")
    return True

def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python playlist-generator.py <tracks_excel> [<mount_directory>]")
        sys.exit(1)
    
    tracks_excel = sys.argv[1]
    
    # Get mount directory from command line or use default
    mount_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/SP3000Util/mnt")
    
    # Check if the mount directory exists
    if not os.path.exists(mount_dir):
        print(f"Error: Mount directory {mount_dir} does not exist")
        sys.exit(1)
    
    # Scan SDXC card for tracks
    sdxc_cd, sdxc_hires, playlist_dir = scan_sdxc_for_tracks(mount_dir)
    
    if len(sdxc_tracks) == 0:
        print(f"No tracks found on SDXC card at {mount_dir}/Music")
        print("Make sure the SDXC card is mounted and contains music files")
        sys.exit(1)
    
    # Extract track info from paths
    extract_track_info_from_paths(sdxc_cd, sdxc_hires)
    
    # Load play count data if available
    load_play_count_data(tracks_excel)
    
    # Create genre playlists
    genres_to_create = ["Electronic", "Jazz", "Hip-Hop", "House", "Soul-Funk"]
    created_count = 0
    
    for genre in genres_to_create:
        if create_flow_optimized_playlist(genre, TRACK_COUNT, playlist_dir, sdxc_cd, sdxc_hires):
            created_count += 1
    
    # Create discovery playlist
    create_discovery_playlist(TRACK_COUNT, playlist_dir, sdxc_cd, sdxc_hires)
    
    # Summary
    print(f"\nCreated {created_count} genre playlists and 1 discovery playlist")
    print(f"All playlists are saved in: {playlist_dir}")
    
    # List all playlists
    print("\nGenerated playlists:")
    for playlist_file in os.listdir(playlist_dir):
        if playlist_file.endswith('.m3u'):
            print(f"  - {playlist_file}")

if __name__ == "__main__":
    main()
