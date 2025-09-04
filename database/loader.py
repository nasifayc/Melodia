import pandas as pd
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from tqdm import tqdm


class Neo4jMusicLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    def close(self):
        self.driver.close()
    def clean_data(self, df):
        """Clean and prepare the music data"""
        df_clean = df.copy()
        df_clean = df_clean.dropna(subset=['track_name', 'track_artist', 'track_album_name','track_id'])
        
        text_columns = ['track_name', 'track_artist', 'track_album_name', 'playlist_genre']
        for col in text_columns:
            if col in text_columns:
                df_clean.loc[:,col] = df_clean[col].str.strip().fillna('Unknown')
        
       
        numeric_defaults = {
            'track_popularity': 0,
            'danceability': 0.5,
            'energy': 0.5,
            'duration_ms': 180000  # 3 minutes default
        }
        
        for col, default_val in numeric_defaults.items():
            if col in df_clean.columns:
                df_clean.loc[:, col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(default_val)
        
        if 'track_album_release_date' in df_clean.columns:
            df_clean.loc[:,'track_album_release_date'] = pd.to_datetime(
                df_clean['track_album_release_date'], errors='coerce'
            ).dt.strftime('%Y-%m-%d').fillna('1900-01-01')
            
        df_clean = df_clean.drop_duplicates(subset=['track_id'])
        
        return df_clean
    
    def load_data(self, df):
        """Load the cleaned data into Neo4j"""
        with self.driver.session() as session:
            
            print("Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n") 
            
            print("Loading artists...")
            artists = df['track_artist'].unique()
            for artist in tqdm(artists, desc="Artists"):
                session.run("MERGE (a:Artist {name: $name})", name=artist)
                
            print("Loading albums...")
            albums = df[['track_album_id','track_album_name', 'track_album_release_date']].drop_duplicates()
            album_records = list(albums.itertuples(index=False))
            for  album in tqdm(album_records, desc="Albums"):
                session.run(
                    "MERGE (al:Album {id: $id,title: $title, releaseDate: $release_date})",
                    id=album.track_album_id,
                    title=album.track_album_name,
                    release_date=album.track_album_release_date
                )
                
            print("Loading songs with audio features...")
            song_records = list(df.itertuples(index=False))
            for song in tqdm(song_records, desc="Songs"):
                session.run(
                    """MERGE (s:Song {
                        id: $id, title: $title, duration: $duration, 
                        popularity: $popularity, genre: $genre, 
                        danceability: $danceability, energy: $energy})""",
                    id=song.track_id,
                    title=song.track_name,
                    duration=getattr(song, 'duration_ms', 180000),
                    popularity=getattr(song, 'track_popularity', 0),
                    genre=getattr(song, 'playlist_genre', 'Unknown'),
                    danceability=getattr(song, 'danceability', 0.5),
                    energy=getattr(song, 'energy', 0.5),
                )
                
                
            print("Creating relationships...")
            batch_size = 1000
            total_songs = len(song_records)
            
            
            for i in tqdm(range(0, total_songs, batch_size), desc="Creating relationships"):
                batch = song_records[i:i+batch_size]
                for song in batch:
                    # Artist -> SINGS -> Song
                    session.run(
                            "MATCH (a:Artist {name: $artist}), (s:Song {id: $song_id}) MERGE (a)-[:SINGS]->(s)",
                            artist=song.track_artist,
                            song_id=song.track_id
                        )
                    # Album -> CONTAINS -> Song
                    session.run(
                            "MATCH (al:Album {id: $album_id}), (s:Song {id: $song_id}) MERGE (al)-[:CONTAINS]->(s)",
                            album_id=song.track_album_id,
                            song_id=song.track_id
                        )
                    # Artist -> CREATED -> Album (if not already linked)
                    session.run(
                        "MATCH (a:Artist {name: $artist}), (al:Album {id: $album_id}) MERGE (a)-[:CREATED]->(al)",
                        artist=song.track_artist,
                        album_id=song.track_album_id
                    )
                    
            
            
def load_music_data():
    loader = Neo4jMusicLoader()
    try:
        print("Reading CSV file...")
        df = pd.read_csv('data/spotify_songs.csv')
        
        print("Cleaning data...")
        cleaned_df = loader.clean_data(df)
        
        print(f"Loaded {len(cleaned_df)} songs from {cleaned_df['track_artist'].nunique()} artists")
        print(f"Genres: {cleaned_df['playlist_genre'].unique().tolist()}")
        
        print("Loading data into Neo4j...")
        loader.load_data(cleaned_df)
        
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loader.close()
            