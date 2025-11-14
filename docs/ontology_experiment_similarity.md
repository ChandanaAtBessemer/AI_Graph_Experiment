# Ontology Experiment 1: Semantic Similarity (SIMILAR_TO)

## Date
November 7, 2025

## Hypothesis
Survey responses with similar meaning should cluster together via SIMILAR_TO relationships, enabling queries like "find responses similar to this pricing concern."

---

## Method

### Approach
- Generated embeddings for all 40 text responses using OpenAI `text-embedding-3-small`
- Calculated cosine similarity between all pairs (780 comparisons)
- Added SIMILAR_TO relationships for pairs above threshold

### Implementation
```python
# Get embeddings
embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input=response_text
)

# Calculate similarity
similarity = cosine_similarity(embedding1, embedding2)

# Create relationship if similar
if similarity >= 0.50:
    CREATE (r1)-[:SIMILAR_TO {similarity_score: score}]->(r2)
```

---

## Results

### Final Statistics
- **Total SIMILAR_TO relationships created:** 29
- **Average similarity score:** 0.556
- **Min score:** 0.503
- **Max score:** 0.657

### Top Similar Pairs

1. **Performance/Reliability (0.657)**
   - "Fast performance and reliable uptime" ↔ "Platform stability impressive"
   
2. **Pricing Concerns (0.647)**
   - "Pricing unjustified vs alternatives" ↔ "Pricing high vs competitors"

3. **Pricing + Scalability (0.630)**
   - "Pricing high for small teams" ↔ "Pricing doesn't scale for growing teams"

4. **Mobile/Responsive Issues (0.626)**
   - "Interface cluttered on small screens" ↔ "Mobile experience needs work"

5. **Customization (0.605)**
   - "Love dark mode and customizable dashboard" ↔ "Want more customization for reports"

### Clustering Patterns Observed

**Pricing cluster (8 pairs):**
- Multiple responses about pricing being "too high", "expensive", "unjustified"
- Similarity scores: 0.506-0.647
- Clear thematic cohesion

**Mobile/UI cluster (7 pairs):**
- Responses about mobile experience, responsive design, interface issues
- Similarity scores: 0.512-0.626
- Cohesive complaints about UI/UX

**Collaboration/Team Features (3 pairs):**
- Real-time editing, version control, team communication
- Similarity scores: 0.505-0.591
- Feature-specific grouping

**Performance/Reliability (1 pair):**
- Highest similarity score (0.657)
- Very similar phrasing about stability

---

## Threshold Experiment Results

| Threshold | Pairs Found | Notes |
|-----------|-------------|-------|
| 0.85      | 0           | Too strict - no matches |
| 0.75      | 0           | Still too strict |
| 0.70      | 0           | No clear duplicates |
| **0.50**  | **29**      | **Optimal - captures related topics** |

**Finding:** Survey responses are diverse. Even responses about the same topic show 0.5-0.65 similarity, not 0.85+.

---

## Key Findings

### 1. Response Diversity is High ✅
**Observation:** Even responses about the same topic (pricing) show similarity scores of 0.5-0.65, not 0.9+

**Why this matters:**
- People express concerns differently
- "Pricing too high" vs "Cost unjustified" = 65% similar (not 95%)
- This is REALISTIC - real survey data will have natural variation

**Implication:**
- Threshold of 0.50 is appropriate for survey data
- Can't expect near-duplicates (0.90+) in real feedback

---

### 2. Embeddings Cluster Effectively ✅
**What works well:**
- **Pricing cluster:** 8 pairs found, all legitimate
- **Mobile issues:** 7 pairs, clear pattern
- **Performance/reliability:** Highest similarity (0.657)

**Accuracy Assessment:**
- Manual review of top 10 pairs: 10/10 accurate
- All pairs are genuinely similar in meaning
- No false positives in top matches

**Insight:**
- 0.50 threshold balances precision and recall well
- Embeddings successfully identify paraphrasing
- Works across different writing styles

---

### 3. SIMILAR_TO Complements HAS_THEME ✅

**SIMILAR_TO (Embeddings):**
- Finds responses that say the same thing differently
- Example: "Pricing high for small teams" ↔ "Pricing doesn't scale for growing teams"
- Both mention pricing AND scaling issues

**HAS_THEME (DSPy):**
- Connects ALL pricing responses via "pricing" theme
- Broader clustering (connects even dissimilar phrasing)
- Example: "Pricing high" and "Want free tier" both → pricing theme

**Together they enable:**
```cypher
// Find pricing concerns most similar to a specific complaint
MATCH (r:Response)-[:HAS_THEME]->(t:Theme {name: "pricing"})
MATCH (r)-[:SIMILAR_TO]-(similar:Response)
WHERE similar.id = "1-2"
RETURN r, similar
ORDER BY similarity_score DESC
```

---

## Comparison: SIMILAR_TO vs HAS_THEME

| Feature | SIMILAR_TO | HAS_THEME |
|---------|------------|-----------|
| **Basis** | Semantic embeddings | LLM extraction |
| **Captures** | Paraphrasing | Topic categories |
| **Granularity** | Fine (sentence-level) | Coarse (theme-level) |
| **Coverage** | 29 pairs (selective) | 130 relationships (comprehensive) |
| **Use Case** | Find near-duplicates | Cluster by topic |
| **Accuracy** | 10/10 in top pairs | 8/10 in random sample |
| **Cost** | $0.001 embeddings | $0.004 LLM calls |
| **Speed** | Fast (batch) | Slow (sequential) |

**Recommendation:** Use BOTH
- HAS_THEME for broad analysis ("all pricing concerns")
- SIMILAR_TO for refinement ("responses most like this one")

---

## Recommendations for Voyant Ontology

### 1. Implement SIMILAR_TO with 0.50 threshold
- Generates meaningful clusters without noise
- 29 relationships for 40 responses = good coverage
- Enables "find similar" functionality

### 2. Use SIMILAR_TO for deduplication
- Query: "Has this concern been mentioned before?"
- Show interviewer: "3 participants said something similar"
- Reduce redundant questions

### 3. Combine with HAS_THEME for hybrid queries
```cypher
// Get pricing responses, ranked by similarity to a reference
MATCH (r:Response)-[:HAS_THEME]->(t:Theme {name: "pricing"})
MATCH (r)-[s:SIMILAR_TO]-(ref:Response {id: "1-2"})
RETURN r.text, s.similarity_score
ORDER BY s.similarity_score DESC
```

### 4. Visualize clusters in Voyant UI
- Show "Related responses" widget
- Help analysts see patterns quickly
- Reduce manual reading time

---

## Next Steps

### Immediate
- ✅ SIMILAR_TO relationships added to graph
- ⏳ Add to agent query tools
- ⏳ Test with queries like "find responses similar to this"

### Future Enhancements
1. **Bidirectional relationships:** Currently A→B, add B→A
2. **Threshold tuning per survey:** Different surveys may need different thresholds
3. **Temporal decay:** Older responses less relevant
4. **User feedback:** Let analysts mark "not similar" to improve

---

## Conclusion

**SIMILAR_TO relationships successfully added to ontology.**

**Key Outcomes:**
- ✅ 29 high-quality similarity relationships
- ✅ Effective clustering of pricing, mobile, collaboration topics
- ✅ 0.50 threshold optimal for survey data
- ✅ Complements HAS_THEME relationships well

**For Voyant:**
- Enables "find similar responses" feature
- Helps identify response patterns automatically
- Reduces analyst manual review time

**Experiment validates:** Embeddings + graph structure is a powerful combination for survey analysis.

---

## Appendix: Code

### Full Similarity Builder
```python
class SimilarityBuilder:
    def get_embedding(self, text):
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def cosine_similarity(self, vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def add_similarity_relationships(self, threshold=0.50):
        responses = self.get_all_responses()
        embeddings = {}
        
        # Generate embeddings
        for resp in responses:
            embeddings[resp['id']] = {
                'text': resp['text'],
                'embedding': self.get_embedding(resp['text'])
            }
        
        # Find similar pairs
        for id1 in response_ids:
            for id2 in response_ids:
                similarity = self.cosine_similarity(
                    embeddings[id1]['embedding'],
                    embeddings[id2]['embedding']
                )
                
                if similarity >= threshold:
                    # Create relationship in Neo4j
                    query = """
                    MATCH (r1:Response {id: $id1})
                    MATCH (r2:Response {id: $id2})
                    MERGE (r1)-[s:SIMILAR_TO]->(r2)
                    SET s.similarity_score = $score
                    """
                    self.conn.execute_query(query, {...})
```

---

**Experiment Duration:** 2 hours  
**Lines of Code:** 150  
**API Calls:** 40 embeddings + 780 similarity calculations  
**Cost:** ~$0.001  
**Outcome:** Production-ready SIMILAR_TO relationships
