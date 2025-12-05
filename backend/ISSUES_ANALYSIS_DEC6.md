# System Issues Analysis - December 6, 2025

## 🔍 Three Critical Issues Identified

### Issue 1: FTS Score Always 0.6 (No Differentiation)

**Problem:**

```
Query: "more about ddd"
All 100 results: FTS Score = 0.6
```

**Root Cause in `graph_search_service.py` lines 215-232:**

```python
CASE
    WHEN toLower(coalesce(n.name, '')) = '{cleaned_text}' THEN 1.0      # Exact match (rare)
    WHEN toLower(coalesce(n.name, '')) CONTAINS '{cleaned_text}' THEN 0.95   # Name contains
    WHEN toLower(coalesce(n.domain, '')) CONTAINS '{cleaned_text}' THEN 0.85  # Domain contains
    WHEN toLower(coalesce(n.description, '')) CONTAINS '{cleaned_text}' THEN 0.75  # Desc contains
    ELSE 0.5  # Default base score
END AS base_fts_score

// Then add 0.1 or 0.2 word match bonus
// Result: 0.5 + 0.1 = 0.6 (most common case)
```

**Why Everyone Gets 0.6:**

- Query: "more about ddd and its example"
- Cleaned text: "more about ddd and its example"
- Very few nodes have this exact phrase in name/domain/description
- So base_fts_score = 0.5 (ELSE case)
- Individual words match: gets +0.1 boost
- **Final: 0.5 + 0.1 = 0.6 for almost all results**

**The Flaw:**

- The CASE statement checks for the FULL cleaned query text
- It should check individual words instead
- Current logic: "domain-driven design" CONTAINS "more about ddd and its example" → FALSE → 0.5
- Should be: "domain-driven design" CONTAINS "ddd" → TRUE → higher score

---

### Issue 2: Relevance Filter 0.5 Still Letting Everything Through

**Current Situation:**

```
100 results found → 0.5 filter → Still ~95-100 results pass
```

**Why:**

- Everyone has FTS = 0.6 (from Issue 1)
- Semantic scores vary but hybrid formula helps them pass
- Formula: `(FTS * 0.6 + Semantic * 0.4)`
- Even with low semantic (0.3): `(0.6 * 0.6) + (0.3 * 0.4) = 0.36 + 0.12 = 0.48`
- Very close to 0.5 threshold!

**Need:**

- Fix FTS scoring first (Issue 1)
- Then 0.5-0.6 threshold will work properly

---

### Issue 3: Context Not Preserved ("it" References Don't Work)

**Problem:**

```
User: "What is DDD?"
Bot: [explains DDD]
User: "Give me examples of it"  ← "it" should refer to DDD
Bot: [doesn't understand "it"]
```

**Root Cause - Context Manager is Initialized Per Request!**

In `chatbot_views.py` line 36-37:

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.context_manager = ContextManager()  # ← NEW INSTANCE EVERY TIME!
```

**Why This Breaks:**

1. Django REST Framework creates a NEW instance of ChatbotAPIView for EACH request
2. Each new instance has a FRESH ContextManager with empty `conversations = {}`
3. Previous conversation history is lost between requests
4. Context manager stores in memory, not database

**The Flow:**

```
Request 1: "What is DDD?"
  → New ChatbotAPIView instance created
  → New ContextManager created (conversations = {})
  → Adds message to context_manager.conversations[session_id]
  → Responds
  → Request ends, ChatbotAPIView instance destroyed
  → Context lost!

Request 2: "Tell me more about it"
  → NEW ChatbotAPIView instance created
  → NEW ContextManager created (conversations = {} again!)
  → session_id not in conversations
  → No previous messages available
  → "it" has no reference
```

**Why Message Shows in Database But Not Context:**

- Messages ARE saved to database (Message.objects.create)
- But context_manager doesn't load from database
- It only has in-memory storage that gets wiped

---

## ✅ Solutions

### Fix 1: FTS Scoring with Word-Level Matching

**Strategy:**

- Check individual query words against node properties
- Give higher scores for name/domain matches
- Lower scores for description-only matches
- Create proper score distribution (not everyone at 0.6)

### Fix 2: Load Context from Database

**Strategy:**

- Make ContextManager load existing messages from database
- Add initialization method to populate from Message model
- Persist context across requests

### Fix 3: Increase Filter After FTS Fix

**Strategy:**

- After fixing FTS scoring, observe new distribution
- If needed, increase threshold to 0.6 or 0.65
- Monitor result counts

---

## 📊 Expected Improvements

### FTS Scoring After Fix:

```
Query: "ddd aggregate example"

Results:
- Aggregate (DDD concept): 0.95 (name exact match "aggregate")
- Entity (DDD concept): 0.85 (related concept)
- Repository Pattern: 0.75 (description contains "aggregate")
- Value Object: 0.70 (description contains "ddd")
- Unrelated concepts: 0.3-0.5
```

### Context After Fix:

```
Request 1: "What is DDD?"
  → Context loaded from database
  → Response saved

Request 2: "Examples of it?"
  → Context loaded: sees "What is DDD?" + previous response
  → Understands "it" = DDD
  → Provides relevant examples
```

---

## 🔧 Implementation Plan

1. **Fix FTS Scoring Logic** (High Priority)

   - Rewrite CASE statement to check individual words
   - Add proper word-level matching
   - Test score distribution

2. **Fix Context Persistence** (Critical Priority)

   - Add `load_from_database()` method to ContextManager
   - Call on initialization with session_id
   - Load recent messages from Message model

3. **Adjust Filter Threshold** (After fixes)
   - Monitor new FTS distribution
   - Adjust to 0.6-0.65 if needed

Ready to implement these fixes!
