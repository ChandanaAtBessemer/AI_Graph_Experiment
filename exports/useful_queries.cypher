
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
