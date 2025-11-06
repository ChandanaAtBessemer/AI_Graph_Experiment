"""
Load mock Voyant data into Neo4j graph database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from src.utils.neo4j_connection import Neo4jConnection

class DataLoader:
    def __init__(self):
        self.conn = Neo4jConnection()
    
    def load_survey_and_questions(self, survey_data):
        """Load survey and its questions"""
        survey = survey_data['survey']
        questions = survey_data['questions']
        
        # Create Survey node
        query = """
        CREATE (s:Survey {
            id: $id,
            title: $title,
            description: $description,
            creator_id: $creator_id,
            is_active: $is_active,
            created_at: $created_at
        })
        RETURN s
        """
        self.conn.execute_query(query, survey)
        print(f"✅ Created Survey: {survey['title']}")
        
        # Create Question nodes and relationships
        for q in questions:
            query = """
            MATCH (s:Survey {id: $survey_id})
            CREATE (q:Question {
                id: $id,
                question_text: $question_text,
                question_type: $question_type,
                order: $order,
                is_required: $is_required
            })
            CREATE (s)-[:HAS_QUESTION]->(q)
            RETURN q
            """
            params = {
                'survey_id': q['survey_id'],
                'id': q['id'],
                'question_text': q['question_text'],
                'question_type': q['question_type'],
                'order': q['order'],
                'is_required': q['is_required']
            }
            self.conn.execute_query(query, params)
        
        print(f"✅ Created {len(questions)} Questions")
    
    def load_sessions_and_responses(self, responses_data):
        """Load sessions, participants, and responses"""
        sessions = responses_data['sessions']
        
        for session in sessions:
            # Create Participant node
            participant_query = """
            MERGE (p:Participant {name: $name})
            RETURN p
            """
            self.conn.execute_query(participant_query, {'name': session['interviewee_name']})
            
            # Create Session node
            session_query = """
            MATCH (s:Survey {id: $survey_id})
            MATCH (p:Participant {name: $participant_name})
            CREATE (sess:Session {
                id: $id,
                status: $status,
                started_at: $started_at,
                completed_at: $completed_at
            })
            CREATE (sess)-[:FOR_SURVEY]->(s)
            CREATE (sess)-[:BY_PARTICIPANT]->(p)
            RETURN sess
            """
            session_params = {
                'survey_id': session['survey_id'],
                'participant_name': session['interviewee_name'],
                'id': session['id'],
                'status': session['status'],
                'started_at': session['started_at'],
                'completed_at': session['completed_at']
            }
            self.conn.execute_query(session_query, session_params)
            
            # Create Response nodes
            for i, response in enumerate(session['responses']):
                response_id = f"{session['id']}-{response['question_id']}"
                
                # Handle both text and numeric responses
                answer_text = response.get('answer_text', '')
                answer_value = response.get('answer_value', None)
                
                response_query = """
                MATCH (sess:Session {id: $session_id})
                MATCH (q:Question {id: $question_id})
                CREATE (r:Response {
                    id: $response_id,
                    text: $text,
                    value: $value,
                    created_at: $created_at
                })
                CREATE (r)-[:IN_SESSION]->(sess)
                CREATE (r)-[:ANSWERS]->(q)
                RETURN r
                """
                response_params = {
                    'session_id': session['id'],
                    'question_id': response['question_id'],
                    'response_id': response_id,
                    'text': answer_text,
                    'value': answer_value,
                    'created_at': response['created_at']
                }
                self.conn.execute_query(response_query, response_params)
        
        print(f"✅ Created {len(sessions)} Sessions with Responses")
    
    def verify_data(self):
        """Verify loaded data"""
        queries = {
            "Surveys": "MATCH (s:Survey) RETURN count(s) as count",
            "Questions": "MATCH (q:Question) RETURN count(q) as count",
            "Sessions": "MATCH (sess:Session) RETURN count(sess) as count",
            "Responses": "MATCH (r:Response) RETURN count(r) as count",
            "Participants": "MATCH (p:Participant) RETURN count(p) as count"
        }
        
        print("\n📊 Data Verification:")
        for label, query in queries.items():
            result = self.conn.execute_query(query)
            count = result[0]['count']
            print(f"  {label}: {count}")
    
    def load_all(self):
        """Load all mock data"""
        print("\n📥 Loading mock data into Neo4j...\n")
        
        # Load survey
        with open('data/mock_survey.json', 'r') as f:
            survey_data = json.load(f)
        self.load_survey_and_questions(survey_data)
        
        # Load responses
        with open('data/mock_responses.json', 'r') as f:
            responses_data = json.load(f)
        self.load_sessions_and_responses(responses_data)
        
        # Verify
        self.verify_data()
        
        print("\n✅ All data loaded successfully!\n")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    loader = DataLoader()
    try:
        loader.load_all()
    finally:
        loader.close()
