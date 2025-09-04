from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD


def setup_database_schema():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    with driver.session() as session:
        try:
            # Create constraints for uniqueness
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Song) REQUIRE s.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (al:Album) REQUIRE al.id IS UNIQUE")
            
            # Create indexes for better query performance
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Song) ON (s.genre)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Song) ON (s.popularity)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Song) ON (s.danceability)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Song) ON (s.energy)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Song) ON (s.tempo)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (a:Artist) ON (a.name)")
            
            print("Database schema optimized with all necessary constraints and indexes!")
        except Exception as e:
            print(f"Error setting up database schema: {e}")
        finally:
            driver.close()