from neo4j import GraphDatabase
import os

class Neo4jConnection:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="experiment123"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def test_connection(self):
        """Test if connection works"""
        with self.driver.session() as session:
            result = session.run("RETURN 'Connection successful!' as message")
            return result.single()["message"]
    
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

if __name__ == "__main__":
    # Test the connection
    conn = Neo4jConnection()
    try:
        message = conn.test_connection()
        print(f"✅ {message}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        conn.close()
