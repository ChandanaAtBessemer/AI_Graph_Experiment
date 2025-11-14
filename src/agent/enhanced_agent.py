"""
Enhanced OpenAI Agent with ontology relationship queries
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from openai import OpenAI
from src.utils.neo4j_connection import Neo4jConnection
import json
from dotenv import load_dotenv

load_dotenv()

class EnhancedGraphAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conn = Neo4jConnection()
        
        # Enhanced tools with ontology relationships
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_all_themes",
                    "description": "Get all themes with response counts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Max themes to return"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_responses_by_theme",
                    "description": "Find responses containing a specific theme",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string", "description": "Theme name"},
                            "limit": {"type": "integer", "description": "Max responses"}
                        },
                        "required": ["theme"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_similar_responses",
                    "description": "Find responses similar to a given response using SIMILAR_TO relationships",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response_text": {"type": "string", "description": "Text to find similar responses to"},
                            "min_similarity": {"type": "number", "description": "Minimum similarity score (0.0-1.0)"},
                            "limit": {"type": "integer", "description": "Max similar responses"}
                        },
                        "required": ["response_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_contradictions",
                    "description": "Find contradictory opinions using CONTRADICTS relationships",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "theme": {"type": "string", "description": "Theme to find contradictions in (optional)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_response_context",
                    "description": "Get full context for a response: themes, similar responses, and contradictions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response_text": {"type": "string", "description": "Response text to analyze"}
                        },
                        "required": ["response_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_themes_by_sentiment",
                    "description": "Get themes filtered by sentiment rating",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "min_rating": {"type": "integer"},
                            "max_rating": {"type": "integer"}
                        },
                        "required": ["min_rating", "max_rating"]
                    }
                }
            }
        ]
    
    # Original tools (from basic agent)
    def get_all_themes(self, limit=10):
        query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme)
        RETURN t.name as theme, count(r) as response_count
        ORDER BY response_count DESC
        LIMIT $limit
        """
        return self.conn.execute_query(query, {'limit': limit})
    
    def find_responses_by_theme(self, theme, limit=5):
        query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme {name: $theme})
        MATCH (r)-[:IN_SESSION]->(sess:Session)
        MATCH (sess)-[:BY_PARTICIPANT]->(p:Participant)
        RETURN r.text as response_text, 
               p.name as participant,
               sess.id as session_id
        LIMIT $limit
        """
        return self.conn.execute_query(query, {'theme': theme, 'limit': limit})
    
    def get_themes_by_sentiment(self, min_rating, max_rating):
        query = """
        MATCH (sess:Session)-[:FOR_SURVEY]->(s:Survey)
        MATCH (sess)<-[:IN_SESSION]-(sentiment_response:Response)
        WHERE sentiment_response.value >= $min_rating 
          AND sentiment_response.value <= $max_rating
        MATCH (sess)<-[:IN_SESSION]-(r:Response)-[:HAS_THEME]->(t:Theme)
        WHERE r.text IS NOT NULL
        RETURN t.name as theme, count(DISTINCT r) as response_count
        ORDER BY response_count DESC
        LIMIT 10
        """
        return self.conn.execute_query(query, {
            'min_rating': min_rating,
            'max_rating': max_rating
        })
    
    # NEW: Ontology-based tools
    def find_similar_responses(self, response_text, min_similarity=0.50, limit=5):
        """Find responses similar to given text using SIMILAR_TO relationships"""
        # First, find the response that matches this text (or closest match)
        query = """
        MATCH (r:Response)
        WHERE r.text CONTAINS $search_text OR $search_text CONTAINS substring(r.text, 0, 30)
        WITH r LIMIT 1
        
        MATCH (r)-[s:SIMILAR_TO]-(similar:Response)
        WHERE s.similarity_score >= $min_similarity
        MATCH (similar)-[:IN_SESSION]->(sess:Session)
        MATCH (sess)-[:BY_PARTICIPANT]->(p:Participant)
        
        RETURN similar.text as response_text,
               s.similarity_score as similarity,
               p.name as participant
        ORDER BY s.similarity_score DESC
        LIMIT $limit
        """
        results = self.conn.execute_query(query, {
            'search_text': response_text[:100],
            'min_similarity': min_similarity,
            'limit': limit
        })
        
        if not results:
            # Fallback: show any similar relationships
            query_fallback = """
            MATCH (r1:Response)-[s:SIMILAR_TO]->(r2:Response)
            WHERE s.similarity_score >= $min_similarity
            MATCH (r2)-[:IN_SESSION]->(sess:Session)
            MATCH (sess)-[:BY_PARTICIPANT]->(p:Participant)
            RETURN r1.text as original_text,
                   r2.text as response_text,
                   s.similarity_score as similarity,
                   p.name as participant
            ORDER BY s.similarity_score DESC
            LIMIT $limit
            """
            results = self.conn.execute_query(query_fallback, {
                'min_similarity': min_similarity,
                'limit': limit
            })
        
        return results
    
    def find_contradictions(self, theme=None):
        """Find contradictory responses"""
        if theme:
            query = """
            MATCH (r1:Response)-[:HAS_THEME]->(:Theme {name: $theme})
            MATCH (r1)-[c:CONTRADICTS]->(r2:Response)
            RETURN r1.text as response_1,
                   r2.text as response_2,
                   c.explanation as explanation
            LIMIT 10
            """
            return self.conn.execute_query(query, {'theme': theme})
        else:
            query = """
            MATCH (r1:Response)-[c:CONTRADICTS]->(r2:Response)
            RETURN r1.text as response_1,
                   r2.text as response_2,
                   c.explanation as explanation
            LIMIT 10
            """
            return self.conn.execute_query(query)
    
    def get_response_context(self, response_text):
        """Get full context: themes, similar responses, contradictions"""
        # Find the response
        query = """
        MATCH (r:Response)
        WHERE r.text CONTAINS $search_text
        WITH r LIMIT 1
        
        // Get themes
        OPTIONAL MATCH (r)-[:HAS_THEME]->(t:Theme)
        WITH r, collect(t.name) as themes
        
        // Get similar responses
        OPTIONAL MATCH (r)-[s:SIMILAR_TO]-(similar:Response)
        WITH r, themes, collect({text: similar.text, score: s.similarity_score}) as similar_responses
        
        // Get contradictions
        OPTIONAL MATCH (r)-[c:CONTRADICTS]-(contra:Response)
        WITH r, themes, similar_responses, 
             collect({text: contra.text, explanation: c.explanation}) as contradictions
        
        RETURN r.text as original_text,
               themes,
               similar_responses,
               contradictions
        """
        results = self.conn.execute_query(query, {'search_text': response_text[:100]})
        return results[0] if results else {}
    
    def execute_tool(self, tool_name, arguments):
        """Execute a tool function"""
        if tool_name == "get_all_themes":
            return self.get_all_themes(**arguments)
        elif tool_name == "find_responses_by_theme":
            return self.find_responses_by_theme(**arguments)
        elif tool_name == "get_themes_by_sentiment":
            return self.get_themes_by_sentiment(**arguments)
        elif tool_name == "find_similar_responses":
            return self.find_similar_responses(**arguments)
        elif tool_name == "find_contradictions":
            return self.find_contradictions(**arguments)
        elif tool_name == "get_response_context":
            return self.get_response_context(**arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def query(self, user_question):
        """Main method: Answer questions using the graph"""
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant analyzing survey data using a graph database.
                
You have access to:
- Themes extracted from responses
- SIMILAR_TO relationships (semantic similarity)
- CONTRADICTS relationships (opposing opinions)

Use these tools to provide insights about:
- What themes appear in responses
- Which responses are similar
- Where contradictory opinions exist
- Patterns across user segments
                
Always cite specific data from the tools."""
            },
            {
                "role": "user",
                "content": user_question
            }
        ]
        
        print(f"\n🤔 Question: {user_question}\n")
        
        # Initial API call
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Calling: {function_name}({function_args})")
                
                function_response = self.execute_tool(function_name, function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
            
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            
            answer = final_response.choices[0].message.content
        else:
            answer = response_message.content
        
        print(f"\n💡 Answer:\n{answer}\n")
        return answer
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    agent = EnhancedGraphAgent()
    
    try:
        # Test ontology-aware queries
        test_queries = [
            "What contradictory opinions exist about the user interface?",
            "Show me responses similar to pricing complaints",
            "Find all contradictions in the data",
            "What's the context around the response 'pricing is too high'?",
        ]
        
        print("🤖 Testing Enhanced Graph Agent with Ontology Queries\n")
        print("=" * 80)
        
        for query in test_queries:
            agent.query(query)
            print("=" * 80)
    
    finally:
        agent.close()
