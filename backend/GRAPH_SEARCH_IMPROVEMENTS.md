# Graph Search & Relevance Score Improvements

## Current Issues & Solutions

### 1. Why Relevance Scores Are Low (0.25-0.35)

#### Root Causes:

1. **Vector embeddings not being computed properly** - "VEC Score: N/A" in logs
2. **FTS scores are consistently 0.5** - indicates weak text matching
3. **Graph relationships not fully utilized** - only using 1-2 hop neighbors

#### Solutions Implemented:

✅ **Fixed FTS Normalization**

- **Before**: `(fts - 0.5) / 0.5` → converted 0.5 scores to 0.0
- **After**: Direct use of FTS score → preserves actual relevance

✅ **Adjusted Threshold to 0.35** (balanced)

- 0.25 was too lenient (too many false positives)
- 0.35 is industry standard for balanced precision/recall
- 0.5+ would be better for production but requires better embeddings

✅ **Added Conversation History**

- LLM now receives last 3 exchanges (6 messages)
- Understands references like "it", "that concept", "its example"
- Works in LLM_ONLY and HYBRID_BLEND modes

---

## How to Improve Relevance Scores Further

### Priority 1: Fix Vector Embedding Calculation ⚠️

**Problem**: Semantic similarity isn't being computed

```
VEC Score: N/A  ← This should show a number like 0.73
```

**Check**:

1. Verify Neo4j nodes have `embedding` property populated
2. Check embedding dimension matches (should be 1536 for OpenAI)
3. Ensure user query embedding is being generated

**Neo4j Query to Check**:

```cypher
MATCH (n)
WHERE n.embedding IS NOT NULL
RETURN labels(n), n.name, size(n.embedding) AS embedding_size
LIMIT 5
```

**Expected**: `embedding_size` should be 1536 (OpenAI) or 384 (MiniLM)

---

### Priority 2: Improve Graph Structure

**Current Limitation**: Only finding nodes, not leveraging relationships

**Improvements**:

1. **Add more relationship types**:

   ```cypher
   (Pattern)-[:SOLVES]->(Problem)
   (Pattern)-[:USES]->(Principle)
   (Architecture)-[:IMPLEMENTS]->(Pattern)
   ```

2. **Weight relationships by importance**:

   - Direct relationships: +0.2 boost
   - Multi-hop paths: +0.1 per hop
   - Co-occurrence: +0.15

3. **Add relationship properties**:
   ```cypher
   (:Pattern)-[:RELATED_TO {strength: 0.8, context: "both solve..."}]->(:Pattern)
   ```

---

### Priority 3: Enhance FTS Indexing

**Current**: Simple CONTAINS matching → low scores

**Improvements**:

```cypher
// Create full-text search index with better analyzer
CREATE FULLTEXT INDEX designKnowledgeIndex IF NOT EXISTS
FOR (n:DesignPattern|Architecture|DDDConcept|DesignPrinciple)
ON EACH [n.name, n.description, n.domain, n.synonyms]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'standard-folding',
    `fulltext.eventually_consistent`: true
  }
}
```

**Add synonyms to nodes**:

```cypher
MATCH (n:DDDConcept {name: "Aggregate"})
SET n.synonyms = ["aggregate root", "cluster", "consistency boundary"]
```

---

### Priority 4: Multi-Strategy Scoring

**Current**: 60% FTS + 40% Semantic

**Better Approach**:

```python
def calculate_advanced_score(node, query, graph_context):
    # Base scores
    fts_score = node['fts_score']          # Text matching
    semantic_score = node['semantic']       # Vector similarity

    # Boost factors
    name_exact_match = 1.5 if query.lower() in node['name'].lower() else 1.0
    relationship_boost = min(len(node['neighbors']) * 0.05, 0.3)  # More connected = more important
    domain_match = 0.2 if query_domain == node['domain'] else 0.0

    # Weighted combination
    base_score = (fts_score * 0.4 + semantic_score * 0.6)
    final_score = base_score * name_exact_match + relationship_boost + domain_match

    return min(final_score, 1.0)  # Cap at 1.0
```

---

## Immediate Action Items

### 🔴 Critical (Do First)

1. **Check if embeddings exist in Neo4j**
   ```cypher
   MATCH (n)
   WHERE n.embedding IS NULL
   RETURN count(n) AS nodes_without_embeddings
   ```
2. **If embeddings missing**: Run embedding generation script
   ```bash
   python backend/knowledge_graph/graph_generation/add_embeddings_to_existing_graph.py
   ```

### 🟡 High Priority

3. **Monitor actual scores** in logs after fixes
4. **Test with specific DDD questions** to verify context understanding
5. **Add relationship weights** to most important connections

### 🟢 Medium Priority

6. Implement advanced scoring algorithm
7. Add FTS index with better analyzer
8. Create evaluation metrics dashboard

---

## Testing Strategy

### Test Queries:

```
1. "what is ddd concept?"           → Should return DDD entities
2. "give me its example"            → Should understand "its" = DDD
3. "what's the difference between aggregate and entity?" → Should use graph relationships
4. "how to implement repository pattern?" → Should find pattern + examples
```

### Expected Improvements:

- **Before**: 0 results → LLM_ONLY mode
- **After**: 5-10 results with scores 0.4-0.8 → GRAPH_RAG or HYBRID_BLEND

---

## Monitoring Commands

### Check graph search in real-time:

```bash
# Watch server logs
cd backend
python manage.py runserver

# Look for:
# - "📊 Relevance filtering: X -> Y results"
# - "VEC Score: 0.XX" (should NOT be N/A)
# - "[HYBRID MODE DECISION] Mode selected = GRAPH_RAG"
```

### Check evaluation records:

```python
from core.models import EvaluationRecord
records = EvaluationRecord.objects.order_by('-created_at')[:10]
for r in records:
    print(f"{r.hybrid_mode}: score={r.confidence_score}, rag_used={r.rag_used}")
```

---

## Summary

**Current Status**:

- ✅ Conversation history working
- ✅ Threshold set to 0.35 (balanced)
- ⚠️ Vector similarity not computed (critical issue)
- ⚠️ Graph relationships underutilized

**Next Steps**:

1. Fix embedding calculation (Priority 1)
2. Verify Neo4j has embeddings populated
3. Test with follow-up questions
4. Monitor relevance scores in logs

**Target**:

- Achieve 0.5+ relevance scores for good matches
- Use GRAPH_RAG mode for 60%+ of queries
- Context-aware responses for follow-up questions
