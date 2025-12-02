import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class QuestionType:
    CONCEPT = "concept"
    DEFINITION = "definition"
    COMPARISON = "comparison"
    HOW_TO = "how_to"
    EXAMPLE = "example"
    DIAGRAM = "diagram"
    GREETING = "greeting"
    OUT_OF_SCOPE_GENERAL = "general"


class IntentClassifier:

    def __init__(self):
        # Map common software design terms → graph labels
        self.topic_mapping = {
            "uml": "UML",
            "class diagram": "UML",
            "sequence diagram": "UML",
            "use case": "UML",
            "use-case": "UML",
            "design pattern": "DesignPattern",
            "singleton": "DesignPattern",
            "factory": "DesignPattern",
            "observer": "DesignPattern",
            "software architecture": "Architecture",
            "architecture": "Architecture",
            "mvc": "Architecture",
            "layered": "Architecture",
            "domain": "Domain",
            "requirement": "Requirement",
            "srp": "SOLID",
            "solid": "SOLID",
            "ocp": "SOLID",
            "lsp": "SOLID",
            "dip": "SOLID",
            "isp": "SOLID",
        }

    # ----------------------------------------------------------
    # 1. Main Entry
    # ----------------------------------------------------------
    def classify_intent(self, user_query: str) -> Dict:
        text = user_query.lower().strip()

        # Greetings / small talk
        if re.match(r"^(hi|hello|hey|yo|sup|morning|evening)\b", text):
            return {"question_type": QuestionType.GREETING}

        # Out of scope (non-software-design)
        if self._is_out_of_scope(text):
            return {"question_type": QuestionType.OUT_OF_SCOPE_GENERAL}

        # Determine question category
        question_type = self._detect_question_type(text)

        # Extract concepts inside the sentence
        extracted_concepts = self._extract_concepts(text)

        # Map text to topic label(s)
        topic_labels = self._detect_topics(text)

        # Extract keywords for FTS
        keywords = self._extract_keywords(text)

        return {
            "question_type": question_type,
            "topic_filter_labels": topic_labels,
            "extracted_concepts": extracted_concepts,
            "keywords": keywords,
            "search_depth": 2,
            "relationship_types": ["RELATED_TO"],
            "min_relevance_score": 0.35,
        }

    # ----------------------------------------------------------
    # 2. Out-of-scope detection
    # ----------------------------------------------------------
    def _is_out_of_scope(self, text: str) -> bool:
        software_design_terms = [
            "design", "uml", "diagram", "pattern", "class", "sequence", "use case",
            "architecture", "model", "solid", "flow", "component", "module"
        ]

        return not any(term in text for term in software_design_terms)

    # ----------------------------------------------------------
    # 3. Determine question category
    # ----------------------------------------------------------
    def _detect_question_type(self, text: str) -> str:
        if any(x in text for x in ["what is", "define", "meaning of"]):
            return QuestionType.DEFINITION
        if any(x in text for x in ["how to", "how do i", "steps to", "explain how"]):
            return QuestionType.HOW_TO
        if any(x in text for x in ["compare", "difference between", "vs "]):
            return QuestionType.COMPARISON
        if any(x in text for x in ["example", "give me an example"]):
            return QuestionType.EXAMPLE
        if any(x in text for x in ["draw", "diagram", "uml"]):
            return QuestionType.DIAGRAM

        return QuestionType.CONCEPT

    # ----------------------------------------------------------
    # 4. Extract relevant concepts
    # ----------------------------------------------------------
    def _extract_concepts(self, text: str) -> List[str]:
        # pick only meaningful nouns/phrases
        candidates = re.findall(r"[a-zA-Z][a-zA-Z\s\-]{2,}", text)
        blacklist = {"what", "define", "give", "example", "how", "why", "when", "between"}
        return [c.strip() for c in candidates if c.strip() not in blacklist]

    # ----------------------------------------------------------
    # 5. Map user text to topic labels (graph nodes)
    # ----------------------------------------------------------
    def _detect_topics(self, text: str) -> List[str]:
        labels = []
        for key, label in self.topic_mapping.items():
            if key in text:
                labels.append(label)

        # fallback — if no topic detected, treat as general design question
        return labels if labels else ["General"]

    # ----------------------------------------------------------
    # 6. Extract keywords for FTS search
    # ----------------------------------------------------------
    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r"[a-zA-Z]{3,}", text)
        stopwords = {"what", "how", "why", "the", "and", "that", "this"}
        return [w for w in words if w not in stopwords]
