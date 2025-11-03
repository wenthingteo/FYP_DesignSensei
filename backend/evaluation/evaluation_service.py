# evaluation_service.py
import threading
import time
import json
import logging
from typing import Optional, Dict, List, Tuple
import os

# embeddings & scoring
from sentence_transformers import SentenceTransformer, util
try:
    from bert_score import score as bert_score_fn
    BERT_AVAILABLE = True
except Exception:
    BERT_AVAILABLE = False

# DB
import psycopg2
from psycopg2.extras import Json

# LLM client (example: OpenAI-like)
import openai

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------- Configuration ----------
EMBED_MODEL_NAME = os.getenv("EVAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_API_KEY = os.getenv("OPENAI_API_KEY", None)  # or adapt to your LLM client
openai.api_key = LLM_API_KEY

DB_CONN = {
    "dbname": os.getenv("PG_DB", "chatdb"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASS", "pass"),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", 5432)),
}

# thresholds & weights
RELEVANCE_WEIGHT = 0.50
RUBRIC_WEIGHT = 0.30
BERT_WEIGHT = 0.20

COMBINED_PASS_THRESHOLD = 0.60
REGEN_THRESHOLD = 0.45
MAX_REGEN_ATTEMPTS = 1

# --------- Helpers ----------
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading embed model...")
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model

def compute_cosine(a: str, b: str) -> float:
    model = get_embedding_model()
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    sim = util.cos_sim(emb_a, emb_b).item()
    # map from [-1,1] to [0,1]
    return max(0.0, (sim + 1.0) / 2.0)

def compute_bertscore(preds: List[str], refs: List[str]) -> float:
    if not BERT_AVAILABLE:
        # fallback: use embedding similarity average
        sims = []
        for p, r in zip(preds, refs):
            sims.append(compute_cosine(p, r))
        return float(sum(sims)/len(sims)) if sims else 0.0
    P, R, F1 = bert_score_fn(preds, refs, lang="en", rescale_with_baseline=True)
    return float(F1.mean().item())

def call_llm_rubric(question: str, answer: str, ground_truth: Optional[str]=None) -> Tuple[float, str]:
    """
    Ask LLM to score usefulness and accuracy (0..1). Return a single numeric summary and a short rationale.
    Example prompt: ask LLM to output JSON: {"score":0.8,"rationale":"..."}
    """
    system = "You are a strict grader for educational answers. Score the answer from 0.0 to 1.0."
    # compact rubric: consider clarity/usefulness/accuracy vs question & ground truth (if present)
    if ground_truth:
        prompt = (
            f"Question: {question}\n\n"
            f"Ground-truth/reference: {ground_truth}\n\n"
            f"Student/LLM answer: {answer}\n\n"
            "Give a single numeric score between 0.0 and 1.0 (higher is better) representing overall usefulness and correctness for a learner, "
            "and one-sentence rationale. Reply in JSON with keys 'score' and 'rationale'."
        )
    else:
        prompt = (
            f"Question: {question}\n\n"
            f"Answer: {answer}\n\n"
            "Give a numeric score between 0 and 1 representing usefulness and correctness; return JSON {\"score\":...,\"rationale\":\"...\"}."
        )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini", # change to your model
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":prompt}
            ],
            max_tokens=200,
            temperature=0.0
        )
        text = resp["choices"][0]["message"]["content"].strip()
        # attempt to parse JSON from response
        try:
            data = json.loads(text)
            score = float(data.get("score", 0.0))
            rationale = data.get("rationale", "")
            return max(0.0, min(1.0, score)), rationale
        except Exception:
            # fallback: attempt to extract a numeric from the text and use remainder as rationale
            import re
            m = re.search(r"([01](?:\.\d+)?)", text)
            score = float(m.group(1)) if m else 0.0
            return max(0.0, min(1.0, score)), text
    except Exception as e:
        logger.error("LLM rubric call failed: %s", e, exc_info=True)
        return 0.0, f"llm_error: {e}"

def db_insert_evaluation(record: Dict):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONN)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO evaluation_results
            (session_id, user_id, question, context, llm_answer, ground_truth,
             relevance_score, bert_score, llm_rubric_score, combined_score,
             passed, evaluation_details, action_taken)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            record.get("session_id"),
            record.get("user_id"),
            record.get("question"),
            record.get("context"),
            record.get("llm_answer"),
            record.get("ground_truth"),
            record.get("relevance_score"),
            record.get("bert_score"),
            record.get("llm_rubric_score"),
            record.get("combined_score"),
            record.get("passed"),
            Json(record.get("evaluation_details", {})),
            record.get("action_taken")
        ))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.exception("Failed to insert evaluation record: %s", e)
    finally:
        if conn:
            conn.close()

# ---------- Main Evaluation class ----------
class EvaluationService:
    def __init__(self):
        self.model = get_embedding_model()
        logger.info("EvaluationService initialized")

    def evaluate_and_store_async(self,
                                 session_id: str,
                                 user_id: Optional[str],
                                 question: str,
                                 context: Optional[str],
                                 llm_answer: str
                                 ):
        # spawn background thread so user isn't blocked
        thread = threading.Thread(
            target=self._evaluate_and_store,
            args=(session_id, user_id, question, context, llm_answer),
            daemon=True
        )
        thread.start()

    def _evaluate_and_store(self, session_id, user_id, question, context, llm_answer):
        # Load ground truth if exists (simple lookup function)
        ground_truth = self._lookup_ground_truth(question, context)

        # 1) Relevance: embedding similarity between (question+context) and answer
        qtxt = question if not context else question + "\n\nContext:\n" + context
        relevance_score = compute_cosine(qtxt, llm_answer)

        # 2) BERTScore vs ground truth (if exists)
        bertscr = 0.0
        if ground_truth:
            bertscr = compute_bertscore([llm_answer], [ground_truth])

        # 3) LLM rubric scoring
        llm_rubric_score, rationale = call_llm_rubric(question, llm_answer, ground_truth)

        # 4) Combined
        combined = (RELEVANCE_WEIGHT * relevance_score +
                    RUBRIC_WEIGHT * llm_rubric_score +
                    BERT_WEIGHT * bertscr)

        passed = combined >= COMBINED_PASS_THRESHOLD

        # 5) If failed but above regen threshold, maybe flag; otherwise attempt regeneration 1 time
        action_taken = "none"
        regen_attempts = 0
        final_answer = llm_answer
        final_combined = combined
        final_relevance = relevance_score
        final_bertscore = bertscr
        final_rubric = llm_rubric_score
        regen_reason = None

        if not passed and combined < REGEN_THRESHOLD and regen_attempts < MAX_REGEN_ATTEMPTS:
            regen_attempts += 1
            regen_reason = "low_combined_score"
            logger.info("Attempting regeneration (attempt %d) due to low combined score %.3f", regen_attempts, combined)
            # regenerate: you must implement regenerate_fn in your application - here we call a simple LLM re-prompt
            new_answer = self._regenerate_answer(question, context, llm_answer)
            # re-evaluate
            final_relevance = compute_cosine(qtxt, new_answer)
            final_bertscore = compute_bertscore([new_answer], [ground_truth]) if ground_truth else 0.0
            final_rubric, rationale = call_llm_rubric(question, new_answer, ground_truth)
            final_combined = (RELEVANCE_WEIGHT * final_relevance +
                              RUBRIC_WEIGHT * final_rubric +
                              BERT_WEIGHT * final_bertscore)
            final_answer = new_answer
            action_taken = "regenerated" if final_combined >= combined else "regenerated_but_not_better"
            passed = final_combined >= COMBINED_PASS_THRESHOLD

        if not passed and final_combined < REGEN_THRESHOLD:
            action_taken = "flagged_for_review"

        # store the evaluation
        record = {
            "session_id": session_id,
            "user_id": user_id,
            "question": question,
            "context": context,
            "llm_answer": final_answer,
            "ground_truth": ground_truth,
            "relevance_score": float(final_relevance),
            "bert_score": float(final_bertscore),
            "llm_rubric_score": float(final_rubric),
            "combined_score": float(final_combined),
            "passed": bool(passed),
            "evaluation_details": {
                "initial_relevance": float(relevance_score),
                "initial_bert": float(bertscr),
                "initial_rubric": float(llm_rubric_score),
                "final_relevance": float(final_relevance),
                "final_bert": float(final_bertscore),
                "final_rubric": float(final_rubric),
                "rationale": rationale,
                "regen_reason": regen_reason,
                "regen_attempts": regen_attempts
            },
            "action_taken": action_taken
        }

        db_insert_evaluation(record)
        logger.info("Evaluation stored for session %s: pass=%s combined=%.3f action=%s", session_id, passed, final_combined, action_taken)

    # --- Lookup functions ---
    def _lookup_ground_truth(self, question: str, context: Optional[str]) -> Optional[str]:
        # Query ground_truths table for the exact question or nearest match (simple exact match here)
        try:
            conn = psycopg2.connect(**DB_CONN)
            cur = conn.cursor()
            cur.execute("SELECT ground_truth FROM ground_truths WHERE question = %s AND verified = true ORDER BY created_at DESC LIMIT 1", (question,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            logger.exception("lookup_ground_truth failed: %s", e)
            return None

    def _regenerate_answer(self, question: str, context: Optional[str], previous_answer: str) -> str:
        # A gentle regeneration prompt that asks the LLM to be concise, cite sources (if available), and improve clarity.
        prompt = f"""Please improve the following answer so it is clearer, more accurate, and directly answers the question.
Question: {question}
Context: {context or '(none)'}
Previous answer: {previous_answer}

Produce a single improved answer. Keep it concise (max 250 words), and if you ARE NOT SURE about facts say 'I might be mistaken' and suggest where to check."""
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                temperature=0.0,
                max_tokens=400
            )
            new_answer = resp["choices"][0]["message"]["content"].strip()
            return new_answer
        except Exception as e:
            logger.exception("Regeneration failed: %s", e)
            return previous_answer

# ---------- Usage example ----------
# In your chatbot backend, after generating the LLM answer, call:
# eval_service = EvaluationService()
# eval_service.evaluate_and_store_async(session_id, user_id, question, context, llm_answer)
