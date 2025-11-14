# Voyant Deployment Package: Graph-RAG with Ontology

## Package Contents

This package contains everything needed to deploy the Graph-RAG system into Voyant production.

---

## 📦 What's Included

### 1. Core Components
```
src/
├── utils/
│   ├── neo4j_connection.py          # Database connection
│   └── export_graph.py               # Visualization exports
├── graph_setup/
│   ├── schema.py                     # Graph schema definition
│   └── load_data.py                  # Data loading scripts
├── dspy_modules/
│   ├── theme_extractor.py            # Theme extraction
│   ├── extract_all_themes.py         # Batch processing
│   ├── add_similarity.py             # Similarity detection
│   └── contradiction_detector.py     # Contradiction detection
└── agent/
    ├── graph_agent.py                # Basic agent
    └── enhanced_agent.py             # Ontology-aware agent
```

### 2. Documentation
```
docs/
├── evaluation_report.md              # Complete evaluation
├── voyant_integration_guide.md       # Integration steps
├── ontology_experiment_similarity.md # SIMILAR_TO experiment
├── ontology_experiment_contradictions.md # CONTRADICTS experiment
├── agent_comparison.md               # Basic vs Enhanced
├── day4_report.md                    # Day 4 work summary
└── voyant_deployment_package.md      # This file
```

### 3. Exports
```
exports/
├── graph_export.json                 # Full graph data
├── gephi_nodes.csv                   # Gephi visualization
├── gephi_edges.csv                   # Gephi visualization
├── ontology_summary.json             # Statistics
└── useful_queries.cypher             # Analyst queries
```

---

## 🚀 Quick Start Deployment

### Prerequisites
```bash
# Required
- Python 3.10+
- Neo4j 5.x (Docker or Cloud)
- OpenAI API key
- Access to Voyant Supabase database

# Optional
- Gephi (for graph visualization)
```

### Step 1: Environment Setup (15 minutes)
```bash
# Clone or copy package
cd voyant_graph_rag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Step 2: Database Setup (30 minutes)
```bash
# Start Neo4j (Docker)
docker run \
    --name voyant-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    -d neo4j:latest

# Initialize schema
PYTHONPATH=. python src/graph_setup/schema.py

# Verify connection
python -c "from src.utils.neo4j_connection import Neo4jConnection; conn = Neo4jConnection(); print('✅ Connected'); conn.close()"
```

### Step 3: Data Migration (1-2 hours)
```bash
# Create sync script from Voyant Supabase → Neo4j
# (Provided in voyant_integration_guide.md)

# Run initial sync
python scripts/sync_voyant_to_neo4j.py --survey_id=1

# Extract themes
PYTHONPATH=. python src/dspy_modules/extract_all_themes.py

# Build ontology relationships
PYTHONPATH=. python src/dspy_modules/add_similarity.py
PYTHONPATH=. python src/dspy_modules/contradiction_detector.py
```

### Step 4: Deploy Agent (30 minutes)
```bash
# Test agent locally
PYTHONPATH=. python src/agent/enhanced_agent.py

# Deploy as API endpoint (FastAPI example)
# (Code provided in integration guide)

# Verify deployment
curl http://localhost:8000/query -d '{"question": "What are the top themes?"}'
```

---

## 🔌 Integration Points

### Option A: API Endpoint
**Add to Voyant backend:**
```python
# backend/app/api/routes/insights.py

from graph_rag.agent import EnhancedGraphAgent

@router.post("/surveys/{survey_id}/insights")
async def get_insights(survey_id: int, question: str):
    agent = EnhancedGraphAgent()
    try:
        answer = agent.query(question)
        return {"answer": answer}
    finally:
        agent.close()
```

### Option B: Background Service
**Run as separate microservice:**
```yaml
# docker-compose.yml
services:
  graph-rag-agent:
    build: ./graph_rag
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8001:8000"
```

### Option C: Scheduled Jobs
**Nightly ontology build:**
```bash
# crontab
0 2 * * * /path/to/venv/bin/python /path/to/build_ontology.py
```

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check Neo4j
curl http://localhost:7474

# Check agent
PYTHONPATH=. python -c "from src.agent.enhanced_agent import EnhancedGraphAgent; agent = EnhancedGraphAgent(); agent.query('What are the top themes?'); agent.close()"

# Check ontology stats
PYTHONPATH=. python -c "from src.utils.export_graph import GraphExporter; exporter = GraphExporter(); exporter.export_ontology_summary(); exporter.close()"
```

### Performance Monitoring
```python
# Log query times
import time

start = time.time()
result = agent.query(question)
duration = time.time() - start

if duration > 5:
    log.warning(f"Slow query: {duration}s - {question}")
```

### Data Quality Checks
```cypher
// Check for orphaned nodes
MATCH (n)
WHERE NOT (n)--()
RETURN count(n) as orphaned_nodes;

// Check relationship counts
MATCH ()-[r]->()
RETURN type(r) as rel_type, count(r) as count
ORDER BY count DESC;

// Check theme coverage
MATCH (r:Response)
WHERE r.text IS NOT NULL
OPTIONAL MATCH (r)-[:HAS_THEME]->()
WITH r, count(*) as theme_count
WHERE theme_count = 0
RETURN count(r) as responses_without_themes;
```

---

## 🔐 Security Considerations

### 1. API Keys
```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use environment variables
export OPENAI_API_KEY="sk-..."
export NEO4J_PASSWORD="..."
```

### 2. Neo4j Access
```python
# Use read-only credentials for agent
NEO4J_AGENT_USER=readonly
NEO4J_AGENT_PASSWORD=...

# Grant limited permissions
CREATE ROLE agent_role;
GRANT MATCH, READ ON GRAPH * TO agent_role;
CREATE USER agent SET PASSWORD 'password' SET ROLE agent_role;
```

### 3. Rate Limiting
```python
# Limit queries per user
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/query")
@limiter.limit("10/minute")
async def query_endpoint(...):
    ...
```

---

## 💰 Cost Management

### OpenAI API Usage
```python
# Track costs
total_tokens = 0

def track_usage(response):
    global total_tokens
    total_tokens += response.usage.total_tokens
    cost = total_tokens * 0.000001  # $1 per 1M tokens
    
    if cost > 10:  # Alert at $10
        send_alert(f"API cost: ${cost:.2f}")
```

### Neo4j Sizing
```
# Development: Neo4j Community (free)
# Production: Neo4j AuraDB Professional
  - 1GB RAM: ~$65/month
  - Scales to ~100K responses
```

---

## 📈 Success Metrics

### Track These KPIs

**Usage Metrics:**
- Queries per day
- Unique users per week
- Most common question types

**Performance Metrics:**
- Average query latency
- P95 query latency
- Error rate

**Value Metrics:**
- Time saved vs manual analysis (survey)
- Insights discovered (contradiction count)
- Duplicate tickets prevented (similarity detection)

---

## 🆘 Troubleshooting

### Common Issues

**1. "Cannot connect to Neo4j"**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check credentials
python -c "from src.utils.neo4j_connection import Neo4jConnection; Neo4jConnection().conn.verify_connectivity()"
```

**2. "Theme extraction returns empty"**
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Test DSPy
PYTHONPATH=. python -c "from src.dspy_modules.theme_extractor import ThemeExtractorModule; extractor = ThemeExtractorModule(); print(extractor.extract('test'))"
```

**3. "Query too slow"**
```cypher
// Add indexes
CREATE INDEX response_text FOR (r:Response) ON (r.text);
CREATE INDEX theme_name FOR (t:Theme) ON (t.name);
```

**4. "Out of memory"**
```bash
# Increase Neo4j heap
docker run -e NEO4J_dbms_memory_heap_max__size=2G ...
```

---

## 📞 Support

### Getting Help

**Documentation:**
- Full evaluation report: `docs/evaluation_report.md`
- Integration guide: `docs/voyant_integration_guide.md`
- Ontology experiments: `docs/ontology_experiment_*.md`

**Code Examples:**
- Basic queries: `exports/useful_queries.cypher`
- Agent usage: `src/agent/enhanced_agent.py`
- Data export: `src/utils/export_graph.py`

**Contact:**
- Technical questions: [Your team channel]
- Bug reports: [GitHub issues]
- Feature requests: [Product board]

---

## �� Next Steps

### After Deployment

**Week 1-2: Validation**
- Monitor query performance
- Gather user feedback
- Identify most-used features

**Week 3-4: Optimization**
- Tune ontology parameters
- Add custom query tools
- Optimize slow queries

**Week 5-6: Expansion**
- Add more relationship types
- Build custom visualizations
- Integrate with Voyant UI

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Neo4j database configured
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Schema initialized
- [ ] Test data loaded
- [ ] Agent tested locally

### Deployment
- [ ] Production database created
- [ ] Data synced from Voyant
- [ ] Ontology relationships built
- [ ] Agent API deployed
- [ ] Monitoring enabled
- [ ] Documentation shared with team

### Post-Deployment
- [ ] Health checks passing
- [ ] First queries successful
- [ ] Team trained on usage
- [ ] Metrics dashboard created
- [ ] Feedback loop established

---

**Package Version:** 1.0   
**Status:** Production-Ready
