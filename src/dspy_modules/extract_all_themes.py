"""
Extract themes from all responses and add to Neo4j graph
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.dspy_modules.theme_extractor import ThemeExtractorModule
from src.utils.neo4j_connection import Neo4jConnection
from tqdm import tqdm

class ThemeGraphBuilder:
    def __init__(self):
        self.extractor = ThemeExtractorModule()
        self.conn = Neo4jConnection()
    
    def get_all_responses(self):
        """Get all text responses from Neo4j"""
        query = """
        MATCH (r:Response)
        WHERE r.text IS NOT NULL AND r.text <> ''
        RETURN r.id as response_id, r.text as text
        """
        return self.conn.execute_query(query)
    
    def add_theme_to_graph(self, theme_name):
        """Create or merge a Theme node"""
        query = """
        MERGE (t:Theme {name: $name})
        RETURN t
        """
        self.conn.execute_query(query, {'name': theme_name})
    
    def link_response_to_theme(self, response_id, theme_name):
        """Create relationship between Response and Theme"""
        query = """
        MATCH (r:Response {id: $response_id})
        MATCH (t:Theme {name: $theme_name})
        MERGE (r)-[:HAS_THEME]->(t)
        """
        self.conn.execute_query(query, {
            'response_id': response_id,
            'theme_name': theme_name
        })
    
    def process_all_responses(self):
        """Extract themes for all responses and add to graph"""
        print("🧠 Extracting themes from all responses...\n")
        
        responses = self.get_all_responses()
        print(f"Found {len(responses)} text responses to process\n")
        
        theme_counts = {}
        
        for response in tqdm(responses, desc="Processing responses"):
            response_id = response['response_id']
            text = response['text']
            
            # Extract themes
            themes = self.extractor.extract(text)
            
            # Add to graph
            for theme in themes:
                # Add theme node
                self.add_theme_to_graph(theme)
                
                # Link response to theme
                self.link_response_to_theme(response_id, theme)
                
                # Track counts
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        print("\n✅ Theme extraction complete!\n")
        return theme_counts
    
    def verify_themes(self):
        """Verify themes were added correctly"""
        queries = {
            "Total Themes": "MATCH (t:Theme) RETURN count(t) as count",
            "Total Theme Relationships": "MATCH ()-[r:HAS_THEME]->() RETURN count(r) as count",
            "Sample Themes": """
                MATCH (t:Theme)
                RETURN t.name as theme
                ORDER BY t.name
                LIMIT 10
            """
        }
        
        print("📊 Verification:")
        for label, query in queries.items():
            result = self.conn.execute_query(query)
            if label == "Sample Themes":
                themes = [r['theme'] for r in result]
                print(f"  {label}: {', '.join(themes)}")
            else:
                print(f"  {label}: {result[0]['count']}")
    
    def show_top_themes(self, limit=10):
        """Show most common themes"""
        query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme)
        RETURN t.name as theme, count(r) as response_count
        ORDER BY response_count DESC
        LIMIT $limit
        """
        results = self.conn.execute_query(query, {'limit': limit})
        
        print(f"\n🔝 Top {limit} Themes:")
        for r in results:
            print(f"  {r['theme']}: {r['response_count']} responses")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    builder = ThemeGraphBuilder()
    try:
        # Extract and add themes
        theme_counts = builder.process_all_responses()
        
        # Verify
        builder.verify_themes()
        
        # Show top themes
        builder.show_top_themes()
        
    finally:
        builder.close()
