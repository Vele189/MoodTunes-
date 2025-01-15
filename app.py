import os
import pandas as pd
import numpy as np
from tqdm import tqdm
import librosa
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename=f'processing_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_audio_path(track_id):
    """Constructs the correct path for a given track ID"""
    tid_str = str(track_id).zfill(6)
    return os.path.join('dataset', 'fma_small', tid_str[:3], f'{tid_str}.mp3')

def load_all_tracks():
    """Load all tracks from FMA dataset"""
    try:
        tracks = pd.read_csv('dataset/fma_metadata/tracks.csv', index_col=0, header=[0, 1])
        logging.info(f"Successfully loaded tracks metadata. Total tracks: {len(tracks)}")
        
        valid_tracks = []
        for track_id in tracks.index:
            file_path = get_audio_path(track_id)
            if os.path.exists(file_path):
                valid_tracks.append({
                    'track_id': track_id,
                    'title': tracks.loc[track_id, ('track', 'title')],
                    'artist': tracks.loc[track_id, ('artist', 'name')],
                    'album': tracks.loc[track_id, ('album', 'title')],
                    'file_path': file_path
                })
        
        logging.info(f"Found {len(valid_tracks)} valid tracks with audio files")
        return valid_tracks
    except Exception as e:
        logging.error(f"Error loading metadata: {str(e)}")
        return []

def extract_mood_features(file_path):
    """Extract audio features relevant to mood analysis"""
    try:
        y, sr = librosa.load(file_path)
        
        features = {}
        
        # Tempo and rhythm features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features['tempo'] = tempo
        
        # Spectral features
        features['spectral_centroid'] = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        features['spectral_bandwidth'] = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        
        # Energy features
        features['rms_energy'] = np.mean(librosa.feature.rms(y=y))
        features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # Tonal features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features['chroma_mean'] = np.mean(chroma)
        
        # MFCCs
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        for i in range(13):
            features[f'mfcc_{i}'] = np.mean(mfccs[i])
        
        return features
        
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return None

def analyze_mood(features):
    """Convert audio features to mood intensities"""
    try:
        moods = {
            'happy_intensity': 0.0,
            'sad_intensity': 0.0,
            'energetic_intensity': 0.0,
            'calm_intensity': 0.0,
            'angry_intensity': 0.0
        }
        
        # High tempo and energy -> energetic/happy
        tempo_factor = min(features['tempo'] / 180.0, 1.0)
        energy_factor = features['rms_energy'] * 10
        
        # Spectral features -> mood mapping
        brightness = features['spectral_centroid'] / 4000
        
        # Calculate intensities
        moods['energetic_intensity'] = min(1.0, (tempo_factor + energy_factor) / 2)
        moods['happy_intensity'] = min(1.0, (brightness + tempo_factor) / 2)
        moods['angry_intensity'] = min(1.0, energy_factor * features['zero_crossing_rate'])
        moods['calm_intensity'] = 1.0 - moods['energetic_intensity']
        moods['sad_intensity'] = 1.0 - moods['happy_intensity']
        
        return moods
        
    except Exception as e:
        logging.error(f"Error analyzing mood: {str(e)}")
        return None

def process_and_store(batch_size=100):
    """Main function to process tracks and store in database"""
    conn = sqlite3.connect('music_mood.db')
    cursor = conn.cursor()
    
    # Load tracks
    print("Loading tracks metadata...")
    tracks = load_all_tracks()
    
    if not tracks:
        print("No tracks found!")
        return
    
    total_tracks = len(tracks)
    processed_count = 0
    error_count = 0
    
    print(f"\nProcessing {total_tracks} tracks...")
    
    # Process in batches
    for i in range(0, total_tracks, batch_size):
        batch = tracks[i:i + batch_size]
        print(f"\nProcessing batch {i//batch_size + 1}/{(total_tracks + batch_size - 1)//batch_size}")
        
        for track in tqdm(batch):
            try:
                # Extract features
                features = extract_mood_features(track['file_path'])
                
                if features is not None:
                    # Analyze mood
                    moods = analyze_mood(features)
                    
                    if moods is not None:
                        # Store track info
                        cursor.execute('''
                            INSERT OR REPLACE INTO songs 
                            (track_id, title, artist, album, file_path)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            track['track_id'],
                            track['title'],
                            track['artist'],
                            track['album'],
                            track['file_path']
                        ))
                        
                        # Store mood analysis
                        cursor.execute('''
                            INSERT INTO mood_analysis 
                            (track_id, happy_intensity, sad_intensity, 
                            energetic_intensity, calm_intensity, angry_intensity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            int(track['track_id']),
                            float(moods['happy_intensity']),
                            float(moods['sad_intensity']),
                            float(moods['energetic_intensity']),
                            float(moods['calm_intensity']),
                            float(moods['angry_intensity'])
                        ))
                        
                        processed_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                logging.error(f"Error processing track {track['track_id']}: {str(e)}")
        
        # Commit after each batch
        conn.commit()
        print(f"Progress: {processed_count}/{total_tracks} tracks processed, {error_count} errors")
    
    conn.close()
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed_count} tracks")
    print(f"Errors: {error_count} tracks")
    print("Check the log file for details about any errors.")

if __name__ == "__main__":
    print("Starting FMA dataset processing...")
    process_and_store()