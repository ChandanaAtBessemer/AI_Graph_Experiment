"""
Export Neo4j graph to various formats for visualization
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.neo4j_connection import Neo4jConnection
import json
import csv

class GraphExporter:
    def __init__(self):
        self.conn = Neo4jConnection()
    
    def export_to_json(self, output_file='graph_export.json'):
        """Export entire graph to JSON format"""
        print("📊 Exporting graph to JSON...\n")
        
        # Get all nodes
        nodes_query = """
        MATCH (n)
        RETURN 
            id(n) as id,
            labels(n) as labels,
            properties(n) as properties
        """
        nodes = self.conn.execute_query(nodes_query)
        
        # Get all relationships
        rels_query = """
        MATCH (source)-[r]->(target)
        RETURN 
            id(source) as source,
            id(target) as target,
            type(r) as type,
            properties(r) as properties
        """
        relationships = self.conn.execute_query(rels_query)
        
        graph_data = {
            'nodes': nodes,
            'relationships': relationships,
            'metadata': {
                'total_nodes': len(nodes),
                'total_relationships': len(relationships),
                'export_date': '2025-11-07'
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)
        
        print(f"✅ Exported {len(nodes)} nodes and {len(relationships)} relationships")
        print(f"   Saved to: {output_file}\n")
        
        return graph_data
    
    def export_to_gephi(self, nodes_file='gephi_nodes.csv', edges_file='gephi_edges.csv'):
        """Export to Gephi CSV format"""
        print("📊 Exporting graph to Gephi format...\n")
        
        # Export nodes
        nodes_query = """
        MATCH (n)
        RETURN 
            id(n) as Id,
            labels(n)[0] as Label,
            CASE 
                WHEN n.name IS NOT NULL THEN n.name
                WHEN n.text IS NOT NULL THEN substring(n.text, 0, 50)
                WHEN n.title IS NOT NULL THEN n.title
                ELSE 'Node_' + toString(id(n))
            END as Label_Display
        """
        nodes = self.conn.execute_query(nodes_query)
        
        # Write nodes CSV
        with open(nodes_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Id', 'Label', 'Label_Display'])
            writer.writeheader()
            writer.writerows(nodes)
        
        print(f"✅ Exported {len(nodes)} nodes to {nodes_file}")
        
        # Export edges
        edges_query = """
        MATCH (source)-[r]->(target)
        RETURN 
            id(source) as Source,
            id(target) as Target,
            type(r) as Type,
            CASE 
                WHEN r.similarity_score IS NOT NULL THEN r.similarity_score
                ELSE 1.0
            END as Weight
        """
        edges = self.conn.execute_query(edges_query)
        
        # Write edges CSV
        with open(edges_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Source', 'Target', 'Type', 'Weight'])
            writer.writeheader()
            writer.writerows(edges)
        
        print(f"✅ Exported {len(edges)} edges to {edges_file}\n")
        
        return len(nodes), len(edges)
    
    def export_ontology_summary(self, output_file='ontology_summary.json'):
        """Export ontology statistics and structure"""
        print("📊 Generating ontology summary...\n")
        
        # Node type counts
        node_counts_query = """
        MATCH (n)
        RETURN labels(n)[0] as node_type, count(*) as count
        ORDER BY count DESC
        """
        node_counts = self.conn.execute_query(node_counts_query)
        
        # Relationship type counts
        rel_counts_query = """
        MATCH ()-[r]->()
        RETURN type(r) as relationship_type, count(*) as count
        ORDER BY count DESC
        """
        rel_counts = self.conn.execute_query(rel_counts_query)
        
        # Theme distribution
        theme_dist_query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme)
        RETURN t.name as theme, count(r) as response_count
        ORDER BY response_count DESC
        LIMIT 20
        """
        theme_dist = self.conn.execute_query(theme_dist_query)
        
        # Similarity stats
        similarity_stats_query = """
        MATCH ()-[s:SIMILAR_TO]->()
        RETURN 
            count(s) as total_similarities,
            avg(s.similarity_score) as avg_score,
            min(s.similarity_score) as min_score,
            max(s.similarity_score) as max_score
        """
        similarity_stats = self.conn.execute_query(similarity_stats_query)
        
        # Contradiction stats
        contradiction_stats_query = """
        MATCH ()-[c:CONTRADICTS]->()
        RETURN count(c) as total_contradictions
        """
        contradiction_stats = self.conn.execute_query(contradiction_stats_query)
        
        summary = {
            'node_types': node_counts,
            'relationship_types': rel_counts,
            'top_themes': theme_dist,
            'similarity_stats': similarity_stats[0] if similarity_stats else {},
            'contradiction_stats': contradiction_stats[0] if contradiction_stats else {},
            'generated_date': '2025-11-07'
        }
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print("Ontology Summary:")
        print(f"  Node Types: {len(node_counts)}")
        print(f"  Relationship Types: {len(rel_counts)}")
        print(f"  Top Theme: {theme_dist[0]['theme']} ({theme_dist[0]['response_count']} responses)")
        print(f"  Total Similarities: {similarity_stats[0]['total_similarities'] if similarity_stats else 0}")
        print(f"  Total Contradictions: {contradiction_stats[0]['total_contradictions'] if contradiction_stats else 0}")
        print(f"\n✅ Saved to: {output_file}\n")
        
        return summary
    
    def export_cypher_queries(self, output_file='useful_queries.cypher'):
        """Export useful Cypher queries for analysts"""
        queries = """
-- Useful Neo4j Cypher Queries for Voyant Graph

-- ===========================================
-- BASIC EXPLORATION
-- ===========================================

-- View all node types and counts
MATCH (n)
RETURN labels(n)[0] as NodeType, count(*) as Count
ORDER BY Count DESC;

-- View all relationship types and counts
MATCH ()-[r]->()
RETURN type(r) as RelationType, count(*) as Count
ORDER BY Count DESC;

-- ===========================================
-- THEME ANALYSIS
-- ===========================================

-- Top 10 themes by response count
MATCH (r:Response)-[:HAS_THEME]->(t:Theme)
RETURN t.name as Theme, count(r) as ResponseCount
ORDER BY ResponseCount DESC
LIMIT 10;

-- Themes in negative responses (ratings 1-3)
MATCH (sess:Session)<-[:IN_SESSION]-(rating:Response)
WHERE rating.value >= 1 AND rating.value <= 3
MATCH (sess)<-[:IN_SESSION]-(r:Response)-[:HAS_THEME]->(t:Theme)
WHERE r.text IS NOT NULL
RETURN t.name as Theme, count(DISTINCT r) as Count
ORDER BY Count DESC;

-- Themes in positive responses (ratings 4-5)
MATCH (sess:Session)<-[:IN_SESSION]-(rating:Response)
WHERE rating.value >= 4 AND rating.value <= 5
MATCH (sess)<-[:IN_SESSION]-(r:Response)-[:HAS_THEME]->(t:Theme)
WHERE r.text IS NOT NULL
RETURN t.name as Theme, count(DISTINCT r) as Count
ORDER BY Count DESC;

-- ===========================================
-- SIMILARITY ANALYSIS
-- ===========================================

-- All similar response pairs (sorted by similarity)
MATCH (r1:Response)-[s:SIMILAR_TO]->(r2:Response)
RETURN r1.text as Response1, r2.text as Response2, s.similarity_score as Similarity
ORDER BY s.similarity_score DESC;

-- Find responses similar to a specific text
MATCH (r:Response)
WHERE r.text CONTAINS 'pricing'
WITH r LIMIT 1
MATCH (r)-[s:SIMILAR_TO]-(similar:Response)
RETURN r.text as Original, similar.text as Similar, s.similarity_score as Similarity
ORDER BY s.similarity_score DESC;

-- Similarity clusters (responses with 3+ similar connections)
MATCH (r:Response)-[:SIMILAR_TO]-(similar)
WITH r, count(similar) as similar_count
WHERE similar_count >= 3
RETURN r.text as Response, similar_count as SimilarResponseCount
ORDER BY similar_count DESC;

-- ===========================================
-- CONTRADICTION ANALYSIS
-- ===========================================

-- All contradictions
MATCH (r1:Response)-[c:CONTRADICTS]->(r2:Response)
RETURN r1.text as Response1, r2.text as Response2, c.explanation as Explanation;

-- Contradictions by theme
MATCH (r1:Response)-[:HAS_THEME]->(t:Theme)
MATCH (r1)-[c:CONTRADICTS]->(r2:Response)
RETURN t.name as Theme, 
       r1.text as Response1, 
       r2.text as Response2, 
       c.explanation as Why
ORDER BY t.name;

-- Count contradictions per theme
MATCH (r1:Response)-[:HAS_THEME]->(t:Theme)
MATCH (r1)-[:CONTRADICTS]->()
RETURN t.name as Theme, count(*) as ContradictionCount
ORDER BY ContradictionCount DESC;

-- ===========================================
-- PARTICIPANT ANALYSIS
-- ===========================================

-- Most active participants
MATCH (p:Participant)-[:BY_PARTICIPANT]-(sess:Session)
RETURN p.name as Participant, count(sess) as SessionCount
ORDER BY SessionCount DESC;

-- Participant response themes
MATCH (p:Participant)<-[:BY_PARTICIPANT]-(sess:Session)<-[:IN_SESSION]-(r:Response)-[:HAS_THEME]->(t:Theme)
WHERE p.name = 'Alice Johnson'
RETURN t.name as Theme, count(r) as MentionCount
ORDER BY MentionCount DESC;

-- ===========================================
-- COMPLEX QUERIES
-- ===========================================

-- Full context for a response (themes + similar + contradictions)
MATCH (r:Response {id: '1-2'})
OPTIONAL MATCH (r)-[:HAS_THEME]->(t:Theme)
OPTIONAL MATCH (r)-[s:SIMILAR_TO]-(sim:Response)
OPTIONAL MATCH (r)-[c:CONTRADICTS]-(con:Response)
RETURN r.text as Response,
       collect(DISTINCT t.name) as Themes,
       collect(DISTINCT {text: sim.text, score: s.similarity_score}) as SimilarResponses,
       collect(DISTINCT {text: con.text, why: c.explanation}) as Contradictions;

-- Response journey through a session
MATCH (sess:Session {id: 1})<-[:IN_SESSION]-(r:Response)-[:ANSWERS]->(q:Question)
RETURN q.order as QuestionOrder, 
       q.question_text as Question,
       r.text as Answer
ORDER BY q.order;

-- Theme co-occurrence (themes that appear together)
MATCH (r:Response)-[:HAS_THEME]->(t1:Theme)
MATCH (r)-[:HAS_THEME]->(t2:Theme)
WHERE t1.name < t2.name
RETURN t1.name as Theme1, t2.name as Theme2, count(r) as CoOccurrence
ORDER BY CoOccurrence DESC
LIMIT 20;

-- ===========================================
-- VISUALIZATION QUERIES
-- ===========================================

-- Theme network (for visualization)
MATCH (r:Response)-[:HAS_THEME]->(t:Theme)
WITH t, count(r) as size
MATCH (r:Response)-[:HAS_THEME]->(t)
MATCH (r)-[:HAS_THEME]->(other:Theme)
WHERE t.name < other.name
RETURN t, other, count(r) as weight
ORDER BY weight DESC
LIMIT 50;

-- Contradiction network
MATCH path = (r1:Response)-[:CONTRADICTS]-(r2:Response)
RETURN path;

-- Similarity network (high similarity only)
MATCH (r1:Response)-[s:SIMILAR_TO]-(r2:Response)
WHERE s.similarity_score > 0.60
RETURN r1, s, r2;
"""
        
        with open(output_file, 'w') as f:
            f.write(queries)
        
        print(f"✅ Exported useful Cypher queries to: {output_file}\n")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    exporter = GraphExporter()
    
    try:
        print("🚀 Exporting Graph Data for Visualization\n")
        print("=" * 80 + "\n")
        
        # Export to different formats
        exporter.export_to_json('exports/graph_export.json')
        exporter.export_to_gephi('exports/gephi_nodes.csv', 'exports/gephi_edges.csv')
        exporter.export_ontology_summary('exports/ontology_summary.json')
        exporter.export_cypher_queries('exports/useful_queries.cypher')
        
        print("=" * 80)
        print("\n✅ All exports complete!\n")
        print("Files created:")
        print("  - exports/graph_export.json (full graph data)")
        print("  - exports/gephi_nodes.csv (Gephi import)")
        print("  - exports/gephi_edges.csv (Gephi import)")
        print("  - exports/ontology_summary.json (statistics)")
        print("  - exports/useful_queries.cypher (analyst queries)\n")
        
    finally:
        exporter.close()
