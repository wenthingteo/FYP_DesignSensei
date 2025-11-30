# evaluation_service.py
import threading
import json
import logging
import os
from typing import Optional, List, Tuple, Dict

from sentence_transformers import SentenceTransformer, util
try:
    from bert_score import score as bert_score_fn
    BERT_AVAILABLE = True
except Exception:
    BERT_AVAILABLE = False

# RAGAS factuality metric (Python 3.11 OK)
try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import factuality
    RAGAS_AVAILABLE = True
except Exception:
    RAGAS_AVAILABLE = False

from openai import OpenAI
from django.utils import timezone
from core.models import EvaluationResult, GroundTruth

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------- EMBED MODEL CONFIG ----------
EMBED_MODEL_NAME = os.getenv("EVAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# OpenAI Client
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=LLM_API_KEY)

# -------- SCORING WEIGHTS ----------
RELEVANCE_WEIGHT = 0.40
RUBRIC_WEIGHT = 0.25
BERT_WEIGHT = 0.15
RAGAS_WEIGHT = 0.20

COMBINED_PASS_THRESHOLD = float(os.getenv("EVAL_PASS_THRESHOLD", 0.60))
REGEN_THRESHOLD = float(os.getenv("EVAL_REGEN_THRESHOLD", 0.45))
MAX_REGEN_ATTEMPTS = int(os.getenv("EVAL_MAX_REGEN", 3))


# -----------------------------------
# Embedding model (global singleton)
# -----------------------------------
_model = None
def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading embedding model...")
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def compute_cosine(a: str, b: str) -> float:
    model = get_embedding_model()
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    sim = util.cos_sim(emb_a, emb_b).item()
    return max(0.0, (sim + 1.0) / 2.0)


def compute_bertscore(preds: List[str], refs: List[str]) -> float:
    if not BERT_AVAILABLE:
        sims = [compute_cosine(p, r) for p, r in zip(preds, refs)]
        return float(sum(sims) / len(sims)) if sims else 0.0

    P, R, F1 = bert_score_fn(preds, refs, lang="en", rescale_with_baseline=True)
    return float(F1.mean().item())


def call_llm_rubric(question: str, answer: str, ground_truth: Optional[str] = None) -> Tuple[float, str]:
    """
    LLM rubric score (0..1).
    """
    system = "You are an automated strict grader. Rate correctness and helpfulness from 0.0 to 1.0."

    if ground_truth:
        user_prompt = (
            f"Question: {question}\n\n"
            f"Reference: {ground_truth}\n\n"
            f"Answer: {answer}\n\n"
            "Return JSON: {\"score\": <0-1>, \"rationale\": \"...\"}"
        )
    else:
        user_prompt = (
            f"Question: {question}\n\n"
            f"Answer: {answer}\n\n"
            "Return JSON: {\"score\": <0-1>, \"rationale\": \"...\"}"
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
            j = json.loads(text)
            score = float(j.get("score", 0.0))
            rationale = j.get("rationale", "")
            return max(0, min(1, score)), rationale
        except Exception:
            import re
            m = re.search(r"([01](?:\.\d+)?)", text)
            score = float(m.group(1)) if m else 0.0
            return score, text

    except Exception as e:
        logger.exception("LLM rubric error: %s", e)
        return 0.0, f"error: {e}"


# -----------------------------------
# RAGAS FACTUALITY (0.1+)
# -----------------------------------
def compute_ragas_factuality(question: str, answer: str, context_text: Optional[str]):
    """
    Returns: (score, {details})
    """
    if not RAGAS_AVAILABLE:
        return 0.0, {"error": "RAGAS not installed"}

    try:
        ds = Dataset.from_dict({
            "question": [question],
            "answer": [answer],
            "contexts": [[context_text or ""]],
        })

        res = evaluate(ds, metrics=[factuality])
        score = float(res["factuality"][0])
        return score, {"factuality": score}

    except Exception as e:
        logger.warning("RAGAS factuality failed: %s", e)
        return 0.0, {"error": str(e)}


# -----------------------------------
# Ground Truth lookup
# -----------------------------------
def _lookup_ground_truth(question: str):
    try:
        gt = GroundTruth.objects.filter(question=question, verified=True).order_by("-created_at").first()
        return gt.ground_truth if gt else None
    except Exception as e:
        logger.exception("GroundTruth lookup error: %s", e)
        return None


# ===================================
#   MAIN EVALUATION SERVICE
# ===================================
class EvaluationService:
    def __init__(self):
        self.model = get_embedding_model()
        logger.info("EvaluationService initialized. RAGAS available=%s", RAGAS_AVAILABLE)

    # ----------------------------------------------------
    # Used inside ChatbotAPIView BEFORE sending to user
    # ----------------------------------------------------
    def evaluate_before_send(self, question, context, draft_answer, max_attempts=3, threshold=0.7):
        attempt = 0
        final_answer = draft_answer
        final_score = 0.0

        ground_truth = _lookup_ground_truth(question)

        while attempt < max_attempts:
            attempt += 1

            # 1) Relevance
            qtxt = question + "\n\nContext:\n" + (context or "")
            relevance = compute_cosine(qtxt, final_answer)

            # 2) BERTScore vs ground truth
            bert = compute_bertscore([final_answer], [ground_truth]) if ground_truth else 0.0

            # 3) LLM rubric
            rubric, rationale = call_llm_rubric(question, final_answer, ground_truth)

            # 4) RAGAS factuality
            ragas_score, ragas_details = compute_ragas_factuality(
                question=question,
                answer=final_answer,
                context_text=context
            )

            combined = (
                RELEVANCE_WEIGHT * relevance +
                RUBRIC_WEIGHT * rubric +
                BERT_WEIGHT * bert +
                RAGAS_WEIGHT * ragas_score
            )

            logger.info(
                "Eval attempt %d => rel=%.3f rub=%.3f bert=%.3f ragas=%.3f combined=%.3f",
                attempt, relevance, rubric, bert, ragas_score, combined
            )

            if combined >= threshold:
                return final_answer, combined, attempt

            # regenerate
            final_answer = self._regenerate_answer(question, context, final_answer)
            final_score = combined

        return final_answer, final_score, attempt

    # ----------------------------------------------------
    # Async DB storage
    # ----------------------------------------------------
    def evaluate_and_store_async(self, session_id, user_id, question, context, llm_answer):
        thread = threading.Thread(
            target=self._evaluate_and_store,
            args=(session_id, user_id, question, context, llm_answer),
            daemon=True
        )
        thread.start()

    def _evaluate_and_store(self, session_id, user_id, question, context, llm_answer):
        gt = _lookup_ground_truth(question)

        qtxt = question + "\n\nContext:\n" + (context or "")

        relevance = compute_cosine(qtxt, llm_answer)
        bert = compute_bertscore([llm_answer], [gt]) if gt else 0.0
        rubric, rationale = call_llm_rubric(question, llm_answer, gt)
        ragas_score, ragas_details = compute_ragas_factuality(question, llm_answer, context)

        combined = (
            RELEVANCE_WEIGHT * relevance +
            RUBRIC_WEIGHT * rubric +
            BERT_WEIGHT * bert +
            RAGAS_WEIGHT * ragas_score
        )
        passed = combined >= COMBINED_PASS_THRESHOLD

        try:
            EvaluationResult.objects.create(
                session_id=session_id,
                user_id=user_id,
                question=question,
                context=context,
                llm_answer=llm_answer,

                relevance_score=relevance,
                bert_score=bert,
                llm_rubric_score=rubric,

                ragas_score=ragas_score,
                ragas_details=ragas_details,

                combined_score=combined,
                passed=passed,
                evaluation_timestamp=timezone.now()
            )
            logger.info("Saved evaluation for session=%s score=%.3f", session_id, combined)

        except Exception as e:
            logger.exception("Failed to save EvaluationResult: %s", e)

    # ----------------------------------------------------
    # Regenerate answer
    # ----------------------------------------------------
    def _regenerate_answer(self, question: str, context: Optional[str], previous_answer: str) -> str:
        prompt = f"""
Improve the answer below so it is clearer, more accurate, and directly addresses the question.

Question: {question}
Context: {context or "(none)"}
Previous answer: {previous_answer}

Return one improved answer only (max 250 words). If unsure about facts, say "I might be mistaken" and recommend where to verify.
"""

        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=350
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.exception("Regeneration failed: %s", e)
            return previous_answer