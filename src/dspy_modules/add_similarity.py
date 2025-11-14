"""
Add semantic similarity relationships to the graph
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from openai import OpenAI
from src.utils.neo4j_connection import Neo4jConnection
from dotenv import load_dotenv
import numpy as np

load_dotenv()

class SimilarityBuilder:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conn = Neo4jConnection()
    
    def get_embedding(self, text):
        """Get embedding for text"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def get_all_responses(self):
        """Get all text responses"""
        query = """
        MATCH (r:Response)
        WHERE r.text IS NOT NULL AND r.text <> ''
        RETURN r.id as id, r.text as text
        """
        return self.conn.execute_query(query)
    
    def add_similarity_relationships(self, threshold=0.75):
        """Add SIMILAR_TO relationships based on embeddings"""
        print("🧮 Calculating embeddings for all responses...\n")
        
        responses = self.get_all_responses()
        
        # Get embeddings
        embeddings = {}
        for i, resp in enumerate(responses):
            print(f"Processing {i+1}/{len(responses)}: {resp['text'][:50]}...")
            embeddings[resp['id']] = {
                'text': resp['text'],
                'embedding': self.get_embedding(resp['text'])
            }
        
        print(f"\n✅ Generated {len(embeddings)} embeddings\n")
        print(f"🔍 Finding similar pairs (threshold: {threshold})...\n")
        
        # Find similar pairs
        similar_count = 0
        response_ids = list(embeddings.keys())
        
        for i, id1 in enumerate(response_ids):
            for id2 in response_ids[i+1:]:
                similarity = self.cosine_similarity(
                    embeddings[id1]['embedding'],
                    embeddings[id2]['embedding']
                )
                
                if similarity >= threshold:
                    # Add SIMILAR_TO relationship
                    query = """
                    MATCH (r1:Response {id: $id1})
                    MATCH (r2:Response {id: $id2})
                    MERGE (r1)-[s:SIMILAR_TO]->(r2)
                    SET s.similarity_score = $score
                    """
                    self.conn.execute_query(query, {
                        'id1': id1,
                        'id2': id2,
                        'score': float(similarity)
                    })
                    
                    similar_count += 1
                    print(f"  ✅ Similar pair #{similar_count} (score: {similarity:.3f}):")
                    print(f"     R1: {embeddings[id1]['text'][:60]}...")
                    print(f"     R2: {embeddings[id2]['text'][:60]}...")
                    print()
        
        print(f"\n✅ Created {similar_count} SIMILAR_TO relationships\n")
        return similar_count
    
    def verify_similarities(self):
        """Show sample similar pairs"""
        query = """
        MATCH (r1:Response)-[s:SIMILAR_TO]->(r2:Response)
        RETURN r1.text as text1, r2.text as text2, s.similarity_score as score
        ORDER BY score DESC
        LIMIT 10
        """
        results = self.conn.execute_query(query)
        
        print("📊 Top 10 Most Similar Response Pairs:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. Similarity: {r['score']:.3f}")
            print(f"   Response 1: {r['text1']}")
            print(f"   Response 2: {r['text2']}\n")
    
    def get_similarity_stats(self):
        """Get statistics about similarities"""
        query = """
        MATCH ()-[s:SIMILAR_TO]->()
        RETURN 
            count(s) as total_relationships,
            avg(s.similarity_score) as avg_score,
            min(s.similarity_score) as min_score,
            max(s.similarity_score) as max_score
        """
        result = self.conn.execute_query(query)[0]
        
        print("📈 Similarity Statistics:")
        print(f"  Total SIMILAR_TO relationships: {result['total_relationships']}")
        print(f"  Average similarity score: {result['avg_score']:.3f}")
        print(f"  Min score: {result['min_score']:.3f}")
        print(f"  Max score: {result['max_score']:.3f}\n")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    builder = SimilarityBuilder()
    try:
        # Add similarities with lower threshold
        count = builder.add_similarity_relationships(threshold=0.75)
        
        # Verify
        if count > 0:
            builder.get_similarity_stats()
            builder.verify_similarities()
        else:
            print("ℹ️  No similar pairs found with threshold 0.75")
            print("   Try threshold 0.70 or 0.65")
    finally:
        builder.close()
