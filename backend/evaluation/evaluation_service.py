# evaluation_service.py
import threading
import json
import logging
import os
from typing import Optional, Dict, List, Tuple

from sentence_transformers import SentenceTransformer, util
try:
    from bert_score import score as bert_score_fn
    BERT_AVAILABLE = True
except Exception:
    BERT_AVAILABLE = False

# Try to import ragas (works on Python 3.11 with ragas installed).
try:
    import ragas
    RAGAS_AVAILABLE = True
except Exception:
    RAGAS_AVAILABLE = False

from openai import OpenAI
from django.utils import timezone
from core.models import EvaluationResult, GroundTruth  # adjust if your app path is different

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------- Configuration ----------
EMBED_MODEL_NAME = os.getenv("EVAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# OpenAI client
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=LLM_API_KEY)

# thresholds & weights (tunable)
RELEVANCE_WEIGHT = 0.40   # embedding relevance
RUBRIC_WEIGHT = 0.25      # LLM rubric
BERT_WEIGHT = 0.15        # BERTScore vs ground truth
RAGAS_WEIGHT = 0.20       # RAGAS context/faithfulness composite

COMBINED_PASS_THRESHOLD = float(os.getenv("EVAL_PASS_THRESHOLD", 0.60))
REGEN_THRESHOLD = float(os.getenv("EVAL_REGEN_THRESHOLD", 0.45))
MAX_REGEN_ATTEMPTS = int(os.getenv("EVAL_MAX_REGEN", 3))

# --------- Helpers ----------
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading embed model...")
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model

def compute_cosine(a: str, b: str) -> float:
    """Compute cosine similarity between two pieces of text using sentence-transformers (0..1)."""
    model = get_embedding_model()
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    sim = util.cos_sim(emb_a, emb_b).item()
    return max(0.0, (sim + 1.0) / 2.0)

def compute_bertscore(preds: List[str], refs: List[str]) -> float:
    """Compute BERTScore F1 mean if available, otherwise fall back to embedding similarity average."""
    if not BERT_AVAILABLE:
        sims = [compute_cosine(p, r) for p, r in zip(preds, refs)]
        return float(sum(sims) / len(sims)) if sims else 0.0
    P, R, F1 = bert_score_fn(preds, refs, lang="en", rescale_with_baseline=True)
    return float(F1.mean().item())

def call_llm_rubric(question: str, answer: str, ground_truth: Optional[str] = None) -> Tuple[float, str]:
    """
    Ask LLM to score correctness/usefulness (0..1). Return (score, rationale).
    Uses a compact system + user prompt and expects JSON or a numeric in text.
    """
    system = "You are an automated strict grader. Rate the answer on usefulness and correctness (0.0-1.0)."
    if ground_truth:
        user_prompt = (
            f"Question: {question}\n\n"
            f"Reference: {ground_truth}\n\n"
            f"Answer: {answer}\n\n"
            "Return JSON: {\"score\": <0-1>, \"rationale\": \"...\"}."
        )
    else:
        user_prompt = (
            f"Question: {question}\n\n"
            f"Answer: {answer}\n\n"
            "Return JSON: {\"score\": <0-1>, \"rationale\": \"...\"}."
        )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.0
        )
        text = resp.choices[0].message.content.strip()
        try:
            data = json.loads(text)
            score = float(data.get("score", 0.0))
            rationale = data.get("rationale", "")
            return max(0.0, min(1.0, score)), rationale
        except Exception:
            import re
            m = re.search(r"([01](?:\.\d+)?)", text)
            score = float(m.group(1)) if m else 0.0
            return max(0.0, min(1.0, score)), text
    except Exception as e:
        logger.exception("LLM rubric call failed: %s", e)
        return 0.0, f"llm_error: {e}"

# --- RAGAS or RAGAS-like metrics ---
def compute_ragas_metrics(question: str, answer: str, context_texts: List[str]) -> Dict[str, float]:
    """
    Return a dictionary with RAGAS-like metrics:
      - context_precision (0..1)
      - context_recall (0..1)
      - answer_faithfulness (0..1) (1 = faithful)
      - context_score (composite)
    If ragas is installed, try to use it; else approximate with embeddings + LLM check.
    """
    # If RAGAS available, try to call it (best-effort)
    if RAGAS_AVAILABLE:
        try:
            # this is a high-level use — actual ragas API may differ slightly; adjust if necessary
            # ragas.evaluate should be able to evaluate answer faithfulness & context usage.
            ragas_res = ragas.evaluate(
                question=question,
                predictions=[answer],
                contexts=context_texts,
                input_type="text",
                metrics=["context_precision", "context_recall", "answer_faithfulness"]
            )
            # normalize keys
            cp = float(ragas_res.get("context_precision", 0.0))
            cr = float(ragas_res.get("context_recall", 0.0))
            af = float(ragas_res.get("answer_faithfulness", 0.0))
            composite = (cp + cr + af) / 3.0
            return {"context_precision": cp, "context_recall": cr, "answer_faithfulness": af, "context_score": composite}
        except Exception as e:
            logger.warning("RAGAS call failed; falling back to internal metrics: %s", e)

    # Fallback (RAGAS-like) implementation:
    # context_precision: proportion of provided context that is relevant to the answer (embedding similarity)
    # context_recall: proportion of key facts in answer that are present in context (approx via embedding)
    # answer_faithfulness: LLM check (0..1) - ask LLM whether answer is supported by context
    model = get_embedding_model()
    # compute embeddings for answer and contexts
    try:
        ans_emb = model.encode(answer, convert_to_tensor=True)
    except Exception:
        ans_emb = None

    cps = []
    for ctx in context_texts:
        if ans_emb is not None:
            try:
                ctx_emb = model.encode(ctx, convert_to_tensor=True)
                sim = util.cos_sim(ans_emb, ctx_emb).item()
                cps.append(max(0.0, (sim + 1.0) / 2.0))
            except Exception:
                continue
    context_precision = float(sum(cps) / len(cps)) if cps else 0.0

    # context_recall approximation: do several short checks using answer sentences as queries
    import re
    sentences = [s.strip() for s in re.split(r'[.?!]\s*', answer) if s.strip()]
    if not sentences:
        context_recall = 0.0
    else:
        hits = 0
        for s in sentences:
            s_emb = model.encode(s, convert_to_tensor=True)
            found_sim = 0.0
            for ctx in context_texts:
                try:
                    ctx_emb = model.encode(ctx, convert_to_tensor=True)
                    sim = util.cos_sim(s_emb, ctx_emb).item()
                    found_sim = max(found_sim, max(0.0, (sim + 1.0) / 2.0))
                except Exception:
                    continue
            if found_sim > 0.45:  # if any context has decent similarity to the sentence
                hits += 1
        context_recall = float(hits) / len(sentences)

    # answer faithfulness: ask LLM whether the answer is supported by the given context
    try:
        system = "You are an assistant that judges whether the answer is supported by the provided context. Answer with JSON {\"faithful\": true/false, \"confidence\": 0-1}."
        user_prompt = (
            f"Context:\n{chr(10).join(context_texts)[:4000]}\n\n"
            f"Answer:\n{answer}\n\n"
            "Question: Is the answer supported by the context? Explain briefly and give a confidence 0..1."
        )
        resp = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=200
        )
        text = resp.choices[0].message.content.strip()
        # try parse confidence
        import re
        m = re.search(r"([01](?:\.\d+)?)", text)
        confidence = float(m.group(1)) if m else 0.0
        faithful = True if "true" in text.lower()[:100] else False
        answer_faithfulness = confidence if faithful else max(0.0, confidence * 0.5)
    except Exception as e:
        logger.warning("Faithfulness LLM check failed: %s", e)
        answer_faithfulness = 0.0

    composite = (context_precision + context_recall + answer_faithfulness) / 3.0
    return {"context_precision": context_precision, "context_recall": context_recall, "answer_faithfulness": answer_faithfulness, "context_score": composite}

def _lookup_ground_truth(question: str, context: Optional[str]) -> Optional[str]:
    """DB lookup helper"""
    try:
        gt = GroundTruth.objects.filter(question=question, verified=True).order_by('-created_at').first()
        return gt.ground_truth if gt else None
    except Exception as e:
        logger.exception("lookup_ground_truth failed: %s", e)
        return None

# ---------- Main Evaluation Service ----------
class EvaluationService:
    def __init__(self):
        self.model = get_embedding_model()
        logger.info("EvaluationService initialized (RAGAS available=%s)", RAGAS_AVAILABLE)

    # --- synchronous evaluation used to decide before sending ---
    def evaluate_before_send(self, question, context, draft_answer, max_attempts=3, threshold=0.7):
        """
        Evaluate and regenerate until reaching threshold or attempts exhausted.
        Returns: final_answer, final_score, attempts_used
        """
        attempt = 0
        final_answer = draft_answer
        final_score = 0.0
        ground_truth = _lookup_ground_truth(question, context)
        context_texts = []
        if context:
            # context expected to be a list serialized as string or a combined string
            if isinstance(context, list):
                context_texts = context
            else:
                context_texts = [context]

        while attempt < max_attempts:
            attempt += 1
            # 1) relevance (embedding between question+context and answer)
            qtxt = question if not context else question + "\n\nContext:\n" + (context if isinstance(context, str) else " ".join(context_texts))
            relevance = compute_cosine(qtxt, final_answer)

            # 2) bert score vs ground truth
            bert = compute_bertscore([final_answer], [ground_truth]) if ground_truth else 0.0

            # 3) llm rubric
            rubric, rationale = call_llm_rubric(question, final_answer, ground_truth)

            # 4) ragas metrics
            ragas_metrics = compute_ragas_metrics(question, final_answer, context_texts)
            ragas_score = ragas_metrics.get("context_score", 0.0)

            # 5) combined hybrid score
            combined = (RELEVANCE_WEIGHT * relevance +
                        RUBRIC_WEIGHT * rubric +
                        BERT_WEIGHT * bert +
                        RAGAS_WEIGHT * ragas_score)

            logger.info("Eval attempt %d: relevance=%.3f rubric=%.3f bert=%.3f ragas=%.3f combined=%.3f",
                        attempt, relevance, rubric, bert, ragas_score, combined)

            if combined >= threshold:
                logger.info("Answer passed on attempt %d with score %.3f", attempt, combined)
                return final_answer, combined, attempt

            # regenerate
            logger.info("Attempt %d failed (%.3f), regenerating...", attempt, combined)
            final_answer = self._regenerate_answer(question, context, final_answer)
            final_score = combined

        logger.warning("All %d attempts failed. Final score: %.3f", max_attempts, final_score)
        return final_answer, final_score, attempt

    # --- Async storage (same as your pattern) ---
    def evaluate_and_store_async(self,
                                 session_id: str,
                                 user_id: Optional[str],
                                 question: str,
                                 context: Optional[str],
                                 llm_answer: str):
        thread = threading.Thread(
            target=self._evaluate_and_store,
            args=(session_id, user_id, question, context, llm_answer),
            daemon=True
        )
        thread.start()

    def _evaluate_and_store(self, session_id, user_id, question, context, llm_answer):
        """Full evaluation + DB save (similar to earlier implementation but includes RAGAS metrics)."""
        ground_truth = _lookup_ground_truth(question, context)
        qtxt = question if not context else question + "\n\nContext:\n" + (context if isinstance(context, str) else " ".join(context))

        # 1) relevance
        relevance_score = compute_cosine(qtxt, llm_answer)
        # 2) bertscore
        bertscr = compute_bertscore([llm_answer], [ground_truth]) if ground_truth else 0.0
        # 3) llm rubric
        llm_rubric_score, rationale = call_llm_rubric(question, llm_answer, ground_truth)
        # 4) ragas metrics
        context_texts = [context] if context and isinstance(context, str) else (context if isinstance(context, list) else [])
        ragas_metrics = compute_ragas_metrics(question, llm_answer, context_texts)
        ragas_score = ragas_metrics.get("context_score", 0.0)

        combined = (RELEVANCE_WEIGHT * relevance_score +
                    RUBRIC_WEIGHT * llm_rubric_score +
                    BERT_WEIGHT * bertscr +
                    RAGAS_WEIGHT * ragas_score)
        passed = combined >= COMBINED_PASS_THRESHOLD

        action_taken = "none"
        regen_attempts = 0
        regen_reason = None
        final_answer = llm_answer
        final_combined = combined
        final_relevance = relevance_score
        final_bertscore = bertscr
        final_rubric = llm_rubric_score

        if not passed and combined < REGEN_THRESHOLD and regen_attempts < MAX_REGEN_ATTEMPTS:
            regen_attempts += 1
            regen_reason = "low_combined_score"
            logger.info("Attempting regeneration (attempt %d) due to low score %.3f", regen_attempts, combined)
            new_answer = self._regenerate_answer(question, context, llm_answer)
            # re-evaluate
            final_relevance = compute_cosine(qtxt, new_answer)
            final_bertscore = compute_bertscore([new_answer], [ground_truth]) if ground_truth else 0.0
            final_rubric, rationale = call_llm_rubric(question, new_answer, ground_truth)
            ragas_metrics2 = compute_ragas_metrics(question, new_answer, context_texts)
            final_ragas = ragas_metrics2.get("context_score", 0.0)
            final_combined = (RELEVANCE_WEIGHT * final_relevance +
                              RUBRIC_WEIGHT * final_rubric +
                              BERT_WEIGHT * final_bertscore +
                              RAGAS_WEIGHT * final_ragas)
            final_answer = new_answer
            action_taken = "regenerated" if final_combined >= combined else "regenerated_but_not_better"
            passed = final_combined >= COMBINED_PASS_THRESHOLD

        if not passed and final_combined < REGEN_THRESHOLD:
            action_taken = "flagged_for_review"

        # store
        try:
            EvaluationResult.objects.create(
                session_id=session_id,
                user_id=user_id,
                question=question,
                context=context,
                llm_answer=final_answer,
                ground_truth=ground_truth,
                relevance_score=final_relevance,
                bert_score=final_bertscore,
                llm_rubric_score=final_rubric,
                ragas_score=ragas_score,
                combined_score=final_combined,
                passed=passed,
                evaluation_details={
                    "initial_relevance": relevance_score,
                    "initial_bert": bertscr,
                    "initial_rubric": llm_rubric_score,
                    "ragas_metrics": ragas_metrics,
                    "final_relevance": final_relevance,
                    "final_bert": final_bertscore,
                    "final_rubric": final_rubric,
                    "rationale": rationale,
                    "regen_reason": regen_reason,
                    "regen_attempts": regen_attempts
                },
                action_taken=action_taken,
                evaluation_timestamp=timezone.now()
            )
            logger.info("✅ Evaluation stored for session %s: pass=%s combined=%.3f action=%s",
                        session_id, passed, final_combined, action_taken)
        except Exception as e:
            logger.exception("Failed to save evaluation result via ORM: %s", e)

    # regeneration helper
    def _regenerate_answer(self, question: str, context: Optional[str], previous_answer: str) -> str:
        prompt = f"""Please improve the following answer so it is clearer, more accurate, and directly answers the question.
Question: {question}
Context: {context or '(none)'}
Previous answer: {previous_answer}

Produce a single improved answer. Keep it concise (max 250 words), and if you ARE NOT SURE about facts say 'I might be mistaken' and suggest where to check."""
        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=400
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Regeneration failed: %s", e)
            return previous_answer
