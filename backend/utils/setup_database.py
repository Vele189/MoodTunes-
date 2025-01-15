import sqlite3
import os

def create_database(db_name='music_mood.db'):
    """Create the music mood database with required tables"""
    
    # Check if database already exists
    if os.path.exists(db_name):
        print(f"Warning: Database {db_name} already exists!")
        user_input = input("Do you want to create a new database? This will delete the existing one. (y/n): ")
        if user_input.lower() != 'y':
            print("Database creation cancelled.")
            return False
        os.remove(db_name)
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Create songs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            track_id INTEGER PRIMARY KEY,
            title TEXT,
            artist TEXT,
            album TEXT,
            file_path TEXT
        )
        ''')
        
        # Create mood_analysis table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER,
            happy_intensity REAL,
            sad_intensity REAL,
            energetic_intensity REAL,
            calm_intensity REAL,
            angry_intensity REAL,
            FOREIGN KEY (track_id) REFERENCES songs (track_id)
        )
        ''')
        
        conn.commit()
        print("Database created successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"Error creating database: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()