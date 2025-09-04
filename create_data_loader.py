from database.loader import load_music_data
from database.schema import setup_database_schema

if __name__ == "__main__":
    print("Setting up database schema...")
    setup_database_schema()
    
    print("Loading music data...")
    load_music_data()
    
    print("👍Database setup and data loading complete.")