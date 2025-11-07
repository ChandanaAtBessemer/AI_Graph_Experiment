"""
OpenAI Agent with custom function calling for Neo4j graph queries
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from openai import OpenAI
from src.utils.neo4j_connection import Neo4jConnection
import json
from dotenv import load_dotenv

load_dotenv()

class GraphQueryAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conn = Neo4jConnection()
        
        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_all_themes",
                    "description": "Get a list of all themes extracted from survey responses, with count of how many responses mention each theme",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of themes to return (default: 10)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_responses_by_theme",
                    "description": "Find all survey responses that mention a specific theme",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "theme": {
                                "type": "string",
                                "description": "The theme to search for (e.g., 'pricing', 'mobile app', 'user interface')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of responses to return (default: 5)"
                            }
                        },
                        "required": ["theme"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_themes_by_sentiment",
                    "description": "Get themes grouped by user sentiment rating (Likert scale 1-5). Shows which themes appear in positive vs negative responses",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "min_rating": {
                                "type": "integer",
                                "description": "Minimum rating (1-5). Use 1-2 for negative, 4-5 for positive"
                            },
                            "max_rating": {
                                "type": "integer",
                                "description": "Maximum rating (1-5). Use 1-2 for negative, 4-5 for positive"
                            }
                        },
                        "required": ["min_rating", "max_rating"]
                    }
                }
            }
        ]
    
    def get_all_themes(self, limit=10):
        """Tool: Get all themes with counts"""
        query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme)
        RETURN t.name as theme, count(r) as response_count
        ORDER BY response_count DESC
        LIMIT $limit
        """
        results = self.conn.execute_query(query, {'limit': limit})
        return results
    
    def find_responses_by_theme(self, theme, limit=5):
        """Tool: Find responses containing a specific theme"""
        query = """
        MATCH (r:Response)-[:HAS_THEME]->(t:Theme {name: $theme})
        MATCH (r)-[:IN_SESSION]->(sess:Session)
        MATCH (sess)-[:BY_PARTICIPANT]->(p:Participant)
        RETURN r.text as response_text, 
               p.name as participant,
               sess.id as session_id
        LIMIT $limit
        """
        results = self.conn.execute_query(query, {'theme': theme, 'limit': limit})
        return results
    
    def get_themes_by_sentiment(self, min_rating, max_rating):
        """Tool: Get themes filtered by sentiment rating"""
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
        results = self.conn.execute_query(query, {
            'min_rating': min_rating,
            'max_rating': max_rating
        })
        return results
    
    def execute_tool(self, tool_name, arguments):
        """Execute a tool function"""
        if tool_name == "get_all_themes":
            return self.get_all_themes(**arguments)
        elif tool_name == "find_responses_by_theme":
            return self.find_responses_by_theme(**arguments)
        elif tool_name == "get_themes_by_sentiment":
            return self.get_themes_by_sentiment(**arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def query(self, user_question):
        """Main method: Answer a question using the graph"""
        messages = [
            {
                "role": "system",
                "content": """You are an AI assistant that helps analyze survey data using a graph database. 
                You have access to survey responses, themes extracted from those responses, and participant information.
                Use the available tools to query the graph and provide helpful insights.
                Always provide specific data from the tools to support your answers."""
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
        
        # Check if tools were called
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            # Execute tools
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Calling tool: {function_name} with args: {function_args}")
                
                # Execute the tool
                function_response = self.execute_tool(function_name, function_args)
                
                # Add tool response to messages
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
            
            # Get final response
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
    agent = GraphQueryAgent()
    
    try:
        # Test queries
        test_queries = [
            "What are the top 5 themes mentioned in the survey responses?",
            "Show me responses that mention pricing concerns",
            "What themes appear most in negative responses (ratings 1-3)?",
            "What themes appear in positive responses (ratings 4-5)?"
        ]
        
        print("🤖 Testing Graph Query Agent\n")
        print("=" * 80)
        
        for query in test_queries:
            agent.query(query)
            print("=" * 80)
    
    finally:
        agent.close()
