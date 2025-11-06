"""
Graph Schema for Voyant Survey Data

Node Types:
- Survey: Represents a survey
- Question: Individual survey questions
- Session: A completed survey session (one participant's responses)
- Response: Individual answer to a question
- Theme: Extracted topic/concept from responses
- Participant: Person who took the survey

Relationships:
- (Survey)-[:HAS_QUESTION]->(Question)
- (Session)-[:FOR_SURVEY]->(Survey)
- (Session)-[:BY_PARTICIPANT]->(Participant)
- (Response)-[:IN_SESSION]->(Session)
- (Response)-[:ANSWERS]->(Question)
- (Response)-[:HAS_THEME]->(Theme)
- (Response)-[:SIMILAR_TO]->(Response)  # Semantic similarity
- (Response)-[:CONTRADICTS]->(Response)
- (Response)-[:SUPPORTS]->(Response)
"""

from src.utils.neo4j_connection import Neo4jConnection

class GraphSchema:
    def __init__(self):
        self.conn = Neo4jConnection()
    
    def create_constraints(self):
        """Create uniqueness constraints for efficient lookups"""
        constraints = [
            "CREATE CONSTRAINT survey_id IF NOT EXISTS FOR (s:Survey) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE",
            "CREATE CONSTRAINT session_id IF NOT EXISTS FOR (sess:Session) REQUIRE sess.id IS UNIQUE",
            "CREATE CONSTRAINT response_id IF NOT EXISTS FOR (r:Response) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT theme_name IF NOT EXISTS FOR (t:Theme) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT participant_name IF NOT EXISTS FOR (p:Participant) REQUIRE p.name IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.conn.execute_query(constraint)
                print(f"✅ Created constraint: {constraint.split('(')[1].split(')')[0]}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️  Constraint already exists: {constraint.split('(')[1].split(')')[0]}")
                else:
                    print(f"❌ Error creating constraint: {e}")
    
    def create_indexes(self):
        """Create indexes for common query patterns"""
        indexes = [
            "CREATE INDEX response_text IF NOT EXISTS FOR (r:Response) ON (r.text)",
            "CREATE INDEX theme_name IF NOT EXISTS FOR (t:Theme) ON (t.name)",
            "CREATE INDEX session_status IF NOT EXISTS FOR (s:Session) ON (s.status)"
        ]
        
        for index in indexes:
            try:
                self.conn.execute_query(index)
                print(f"✅ Created index")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️  Index already exists")
                else:
                    print(f"❌ Error creating index: {e}")
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        print("🗑️  Clearing database...")
        self.conn.execute_query("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")
    
    def setup(self, clear_first=False):
        """Set up the complete schema"""
        if clear_first:
            self.clear_database()
        
        print("\n🗂️  Setting up graph schema...")
        self.create_constraints()
        self.create_indexes()
        print("✅ Schema setup complete!\n")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    schema = GraphSchema()
    try:
        # Setup schema (clear_first=True will wipe existing data)
        schema.setup(clear_first=True)
        
        # Verify setup
        print("\n📊 Verifying schema...")
        result = schema.conn.execute_query("SHOW CONSTRAINTS")
        print(f"✅ Total constraints: {len(result)}")
        
    finally:
        schema.close()
