import logging
from typing import List
from datasets import Dataset

from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness

from sentence_transformers import SentenceTransformer
from openai import OpenAI

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Works with RAGAS 0.3.9 (NEW version)
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

        # Load embedding model once
        logger.info("Initializing SentenceTransformer for embeddings...")
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        logger.info("EvaluationService ready. RAGAS 0.3.9 active.")

    # --------------------------
    # LLM CALL (for Ragas)
    # --------------------------
    async def llm_callable(self, prompt: str) -> str:
        """
        RAGAS expects: async fn(prompt) -> string
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    # --------------------------
    # EMBEDDING CALL (for Ragas)
    # --------------------------
    async def embed_callable(self, texts: List[str]) -> List[List[float]]:
        """
        RAGAS expects: async fn(list[str]) -> list[list[float]]
        """
        return self.embedding_model.encode(texts, convert_to_numpy=False).tolist()

    # --------------------------
    # MAIN EVALUATION METHOD
    # --------------------------
    async def evaluate_answer(self, user_question: str, generated_answer: str, context_chunks: List[str]):
        """
        Runs RAGAS evaluation on LLM result.
        """

        logger.info("Running RAGAS evaluation (0.3.9)...")

        # Prepare dataset
        ragas_input = Dataset.from_dict({
            "question": [user_question],
            "answer": [generated_answer],
            "contexts": [context_chunks],
        })

        # Run evaluation
        result = await evaluate(
            dataset=ragas_input,
            metrics=[
                answer_relevancy,
                faithfulness
            ],
            llm=self.llm_callable,
            embed=self.embed_callable
        )

        relevancy = result["answer_relevancy"][0]
        faithful = result["faithfulness"][0]

        # Combine (simple weighted average)
        combined = (relevancy * 0.6) + (faithful * 0.4)

        logger.info(f"RAGAS Evaluation => rel={relevancy:.3f} faith={faithful:.3f} combined={combined:.3f}")

        return {
            "relevance": float(relevancy),
            "faithfulness": float(faithful),
            "combined": float(combined)
        }
