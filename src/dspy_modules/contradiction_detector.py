"""
DSPy module for detecting contradictions between survey responses
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import dspy
from dotenv import load_dotenv
from src.utils.neo4j_connection import Neo4jConnection

load_dotenv()

# Configure DSPy
lm = dspy.LM('openai/gpt-4o-mini', api_key=os.getenv('OPENAI_API_KEY'))
dspy.configure(lm=lm)

class ContradictionDetector(dspy.Signature):
    """Detect if two survey responses express contradictory opinions.
    
    Contradictions occur when:
    - One response praises a feature, another criticizes it
    - One says something is easy, another says it's difficult
    - One says pricing is fair, another says it's too expensive
    
    NOT contradictions:
    - Different topics (UI vs pricing)
    - Different aspects of same feature (like speed, dislike color)
    - Neutral statements
    """
    
    response_1 = dspy.InputField(desc="First survey response")
    response_2 = dspy.InputField(desc="Second survey response")
    contradicts = dspy.OutputField(desc="Boolean: True if responses contradict each other, False otherwise")
    explanation = dspy.OutputField(desc="Brief explanation of why they do or don't contradict")

class ContradictionDetectorModule:
    def __init__(self):
        self.predictor = dspy.ChainOfThought(ContradictionDetector)
    
    def detect(self, response_1, response_2):
        """Detect if two responses contradict each other"""
        result = self.predictor(response_1=response_1, response_2=response_2)
        
        # Parse boolean result
        contradicts_str = result.contradicts.lower().strip()
        contradicts = contradicts_str in ['true', 'yes', '1']
        
        return {
            'contradicts': contradicts,
            'explanation': result.explanation
        }

class ContradictionGraphBuilder:
    def __init__(self):
        self.detector = ContradictionDetectorModule()
        self.conn = Neo4jConnection()
    
    def get_responses_by_theme(self, theme):
        """Get all responses for a specific theme"""
        query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme {name: $theme})
        WHERE r.text IS NOT NULL AND r.text <> ''
        RETURN r.id as id, r.text as text
        """
        return self.conn.execute_query(query, {'theme': theme})
    
    def add_contradiction_relationship(self, id1, id2, explanation):
        """Add CONTRADICTS relationship to graph"""
        query = """
        MATCH (r1:Response {id: $id1})
        MATCH (r2:Response {id: $id2})
        MERGE (r1)-[c:CONTRADICTS]->(r2)
        SET c.explanation = $explanation
        """
        self.conn.execute_query(query, {
            'id1': id1,
            'id2': id2,
            'explanation': explanation
        })
    
    def find_contradictions_for_theme(self, theme):
        """Find all contradictions within a theme"""
        print(f"\n🔍 Finding contradictions in theme: '{theme}'\n")
        
        responses = self.get_responses_by_theme(theme)
        print(f"Found {len(responses)} responses with theme '{theme}'\n")
        
        if len(responses) < 2:
            print(f"⚠️  Need at least 2 responses to detect contradictions\n")
            return 0
        
        contradiction_count = 0
        
        # Compare all pairs
        for i, resp1 in enumerate(responses):
            for resp2 in responses[i+1:]:
                print(f"Comparing:")
                print(f"  R1: {resp1['text'][:70]}...")
                print(f"  R2: {resp2['text'][:70]}...")
                
                result = self.detector.detect(resp1['text'], resp2['text'])
                
                if result['contradicts']:
                    print(f"  ✅ CONTRADICTION DETECTED!")
                    print(f"     Reason: {result['explanation']}\n")
                    
                    self.add_contradiction_relationship(
                        resp1['id'],
                        resp2['id'],
                        result['explanation']
                    )
                    contradiction_count += 1
                else:
                    print(f"  ➖ No contradiction")
                    print(f"     Reason: {result['explanation']}\n")
        
        return contradiction_count
    
    def verify_contradictions(self):
        """Show detected contradictions"""
        query = """
        MATCH (r1:Response)-[c:CONTRADICTS]->(r2:Response)
        RETURN r1.text as text1, r2.text as text2, c.explanation as explanation
        LIMIT 10
        """
        results = self.conn.execute_query(query)
        
        if not results:
            print("ℹ️  No contradictions found\n")
            return
        
        print(f"\n📊 Detected Contradictions:\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. Contradiction:")
            print(f"   Response 1: {r['text1']}")
            print(f"   Response 2: {r['text2']}")
            print(f"   Explanation: {r['explanation']}\n")
    
    def get_contradiction_stats(self):
        """Get statistics about contradictions"""
        query = """
        MATCH ()-[c:CONTRADICTS]->()
        RETURN count(c) as total_contradictions
        """
        result = self.conn.execute_query(query)[0]
        
        print(f"📈 Contradiction Statistics:")
        print(f"  Total CONTRADICTS relationships: {result['total_contradictions']}\n")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    builder = ContradictionGraphBuilder()
    
    try:
        # Test on pricing theme (most likely to have contradictions)
        print("🧪 Experiment: Detecting Contradictions in Survey Responses\n")
        print("=" * 80)
        
        # Focus on pricing theme
        count = builder.find_contradictions_for_theme("pricing")
        
        print("=" * 80)
        print(f"\n✅ Found {count} contradictions in 'pricing' theme\n")
        
        if count > 0:
            builder.get_contradiction_stats()
            builder.verify_contradictions()
    
    finally:
        builder.close()
