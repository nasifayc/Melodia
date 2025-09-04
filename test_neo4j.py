# test_neo4j.py
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# import pandas as pd

def test_neo4j_connection():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    print("=" * 60)
    print("NEO4J DATABASE COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    
    with driver.session() as session:
        # 1. Database Overview
        print("\n1. DATABASE OVERVIEW")
        print("-" * 40)
        
        # Total nodes and relationships
        result = session.run("MATCH (n) RETURN count(n) as total_nodes")
        total_nodes = result.single()["total_nodes"]
        print(f"Total nodes: {total_nodes}")
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
        total_rels = result.single()["total_relationships"]
        print(f"Total relationships: {total_rels}")
        
        # 2. Node Types Breakdown
        print("\n2. NODE TYPES BREAKDOWN")
        print("-" * 40)
        
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(*) as count
            ORDER BY count DESC
        """)
        
        node_types = []
        for record in result:
            node_types.append((record["node_type"], record["count"]))
            print(f"  {record['node_type']}: {record['count']}")
        
        # 3. Relationship Types
        print("\n3. RELATIONSHIP TYPES")
        print("-" * 40)
        
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(*) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            print(f"  {record['rel_type']}: {record['count']}")
        
        # 4. Genre Analysis
        print("\n4. GENRE ANALYSIS")
        print("-" * 40)
        
        result = session.run("""
            MATCH (s:Song)
            RETURN s.genre as genre, count(*) as song_count
            ORDER BY song_count DESC
        """)
        
        genres = []
        for record in result:
            genres.append((record["genre"], record["song_count"]))
            print(f"  {record['genre']}: {record['song_count']} songs")
        
        # 5. Artist Statistics
        print("\n5. ARTIST STATISTICS")
        print("-" * 40)
        
        # Top artists by song count
        result = session.run("""
            MATCH (a:Artist)-[:SINGS]->(s:Song)
            RETURN a.name as artist, count(s) as song_count
            ORDER BY song_count DESC
            LIMIT 15
        """)
        
        print("Top artists by number of songs:")
        for record in result:
            print(f"  {record['artist']}: {record['song_count']} songs")
        
        # 6. Song Properties Sample
        print("\n6. SONG PROPERTIES SAMPLE")
        print("-" * 40)
        
        result = session.run("""
            MATCH (s:Song)
            RETURN s.id as id, s.title as title, s.genre as genre, s.popularity as popularity
            LIMIT 5
        """)
        
        print("Sample songs:")
        for record in result:
            print(f"  {record['title']} ({record['genre']}) - Popularity: {record['popularity']}")
        
        # 7. Specific Genre Check (Pop)
        print("\n7. POP GENRE DETAILED ANALYSIS")
        print("-" * 40)
        
        # Count pop songs
        result = session.run("MATCH (s:Song {genre: 'pop'}) RETURN count(s) as pop_songs")
        pop_count = result.single()["pop_songs"]
        print(f"Total pop songs: {pop_count}")
        
        # Artists with most pop songs
        result = session.run("""
            MATCH (a:Artist)-[:SINGS]->(s:Song {genre: 'pop'})
            RETURN a.name as artist, count(s) as pop_song_count
            ORDER BY pop_song_count DESC
            LIMIT 10
        """)
        
        print("Artists with most pop songs:")
        for record in result:
            print(f"  {record['artist']}: {record['pop_song_count']} pop songs")
        
        # 8. Database Schema Info
        print("\n8. DATABASE SCHEMA INFORMATION")
        print("-" * 40)
        
        # Node properties
        result = session.run("""
            CALL db.schema.nodeTypeProperties()
            YIELD nodeType, propertyName, propertyTypes
            RETURN nodeType, propertyName, propertyTypes
            ORDER BY nodeType, propertyName
        """)
        
        print("Node properties:")
        current_node = None
        for record in result:
            if record["nodeType"] != current_node:
                current_node = record["nodeType"]
                print(f"  {current_node}:")
            print(f"    - {record['propertyName']}: {record['propertyTypes']}")
        
        # 9. Relationship Properties
        print("\n9. RELATIONSHIP PROPERTIES")
        print("-" * 40)
        
        result = session.run("""
            CALL db.schema.relTypeProperties()
            YIELD relType, propertyName, propertyTypes
            RETURN relType, propertyName, propertyTypes
            ORDER BY relType, propertyName
        """)
        
        print("Relationship properties:")
        for record in result:
            print(f"  {record['relType']}: {record['propertyName']} ({record['propertyTypes']})")
        
        # 10. Test the specific query that's failing
        print("\n10. TESTING SPECIFIC QUERIES")
        print("-" * 40)
        
        test_queries = [
            "MATCH (a:Artist)-[:SINGS]->(s:Song {genre: 'pop'}) RETURN a.name LIMIT 10",
            "MATCH (s:Song) WHERE s.genre = 'pop' RETURN count(s)",
            "MATCH (a:Artist) RETURN count(a)",
            "MATCH (al:Album) RETURN count(al)"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                result = session.run(query)
                if "count" in query.lower():
                    count = result.single()[0]
                    print(f"Query {i}: {count} results")
                else:
                    records = list(result)
                    print(f"Query {i}: {len(records)} results")
            except Exception as e:
                print(f"Query {i} failed: {e}")
    
    driver.close()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_neo4j_connection()