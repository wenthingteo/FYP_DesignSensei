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

from openai import OpenAI
from django.utils import timezone
from core.models import EvaluationResult, GroundTruth  # <-- Make sure this path matches your app name

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------- Configuration ----------
EMBED_MODEL_NAME = os.getenv("EVAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# OpenAI setup (new API)
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=LLM_API_KEY)

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
        sims = [compute_cosine(p, r) for p, r in zip(preds, refs)]
        return float(sum(sims) / len(sims)) if sims else 0.0
    P, R, F1 = bert_score_fn(preds, refs, lang="en", rescale_with_baseline=True)
    return float(F1.mean().item())


def call_llm_rubric(question: str, answer: str, ground_truth: Optional[str] = None) -> Tuple[float, str]:
    """Ask LLM to score usefulness and accuracy (0..1). Return (score, rationale)."""
    system = "You are a strict grader for educational answers. Score the answer from 0.0 to 1.0."
    if ground_truth:
        user_prompt = (
            f"Question: {question}\n\n"
            f"Ground-truth/reference: {ground_truth}\n\n"
            f"Answer: {answer}\n\n"
            "Provide JSON: {\"score\": <0-1>, \"rationale\": \"...\"}."
        )
    else:
        user_prompt = (
            f"Question: {question}\n\n"
            f"Answer: {answer}\n\n"
            "Provide JSON: {\"score\": <0-1>, \"rationale\": \"...\"}."
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
        logger.error("LLM rubric call failed: %s", e, exc_info=True)
        return 0.0, f"llm_error: {e}"


# ---------- Main Evaluation Service ----------
class EvaluationService:
    def __init__(self):
        self.model = get_embedding_model()
        logger.info("EvaluationService initialized")

    def evaluate_and_store_async(self,
                                 session_id: str,
                                 user_id: Optional[str],
                                 question: str,
                                 context: Optional[str],
                                 llm_answer: str):
        """Spawn a thread so the evaluation runs asynchronously."""
        thread = threading.Thread(
            target=self._evaluate_and_store,
            args=(session_id, user_id, question, context, llm_answer),
            daemon=True
        )
        thread.start()

    def _evaluate_and_store(self, session_id, user_id, question, context, llm_answer):
        ground_truth = self._lookup_ground_truth(question, context)

        # 1️⃣ Compute relevance
        qtxt = question if not context else question + "\n\nContext:\n" + context
        relevance_score = compute_cosine(qtxt, llm_answer)

        # 2️⃣ Compute BERTScore if ground truth available
        bertscr = compute_bertscore([llm_answer], [ground_truth]) if ground_truth else 0.0

        # 3️⃣ Ask LLM rubric for scoring
        llm_rubric_score, rationale = call_llm_rubric(question, llm_answer, ground_truth)

        # 4️⃣ Combine weighted scores
        combined = (RELEVANCE_WEIGHT * relevance_score +
                    RUBRIC_WEIGHT * llm_rubric_score +
                    BERT_WEIGHT * bertscr)
        passed = combined >= COMBINED_PASS_THRESHOLD

        # 5️⃣ Optional regeneration logic
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
            logger.info("Attempting regeneration (attempt %d) due to low score %.3f", regen_attempts, combined)
            new_answer = self._regenerate_answer(question, context, llm_answer)

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

        # 6️⃣ Store results in database using Django ORM
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
                combined_score=final_combined,
                passed=passed,
                evaluation_details={
                    "initial_relevance": relevance_score,
                    "initial_bert": bertscr,
                    "initial_rubric": llm_rubric_score,
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

    # --- Lookup Ground Truth ---
    def _lookup_ground_truth(self, question: str, context: Optional[str]) -> Optional[str]:
        try:
            gt = GroundTruth.objects.filter(question=question, verified=True).order_by('-created_at').first()
            return gt.ground_truth if gt else None
        except Exception as e:
            logger.exception("lookup_ground_truth failed: %s", e)
            return None

    # --- Regenerate Answer if Low Quality ---
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
        
    def evaluate_before_send(self, question, context, draft_answer, max_attempts=3, threshold=0.7):
        """Evaluate and regenerate until reaching threshold or max_attempts."""
        attempt = 0
        final_answer = draft_answer
        final_score = 0.0

        ground_truth = self._lookup_ground_truth(question, context)
        qtxt = question if not context else question + "\n\nContext:\n" + context

        while attempt < max_attempts:
            attempt += 1
            relevance = compute_cosine(qtxt, final_answer)
            bert = compute_bertscore([final_answer], [ground_truth]) if ground_truth else 0.0
            rubric, rationale = call_llm_rubric(question, final_answer, ground_truth)

            combined = (RELEVANCE_WEIGHT * relevance +
                        RUBRIC_WEIGHT * rubric +
                        BERT_WEIGHT * bert)

            if combined >= threshold:
                logger.info("Answer passed on attempt %d with score %.3f", attempt, combined)
                return final_answer, combined, attempt

            # regenerate if below threshold
            logger.info("Attempt %d failed (%.3f), regenerating...", attempt, combined)
            final_answer = self._regenerate_answer(question, context, final_answer)
            final_score = combined

        logger.warning("All %d attempts failed. Final score: %.3f", max_attempts, final_score)
        return final_answer, final_score, attempt
