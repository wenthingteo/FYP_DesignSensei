# intent_classifier.py (patched to match your real Neo4j labels)
import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    APPLICATION = "application"
    ANALYSIS = "analysis"
    TROUBLESHOOTING = "troubleshooting"
    GREETING = "greeting"
    OUT_OF_SCOPE_GENERAL = "out_of_scope_general"
    UNKNOWN = "unknown"

class SoftwareDesignTopic(Enum):
    DESIGN_PATTERNS = "design_patterns"
    SOLID_PRINCIPLES = "solid_principles"
    ARCHITECTURE = "architecture"
    DDD = "ddd"
    QUALITY = "quality"
    CODE_STRUCTURE = "code_structure"
    GENERAL = "general_software_design"

class IntentClassifier:
    def __init__(self):

        # 🔹 Better pattern detection
        self.question_patterns = {
            QuestionType.EXPLANATION: [r"\bwhat is\b", r"\bexplain\b", r"\bdefine\b", r"\bdescribe\b", r"\bhow does\b"],
            QuestionType.COMPARISON: [r"\bdifference\b", r"\bcompare\b", r"\bvs\b", r"\bversus\b"],
            QuestionType.APPLICATION: [r"\bhow to\b", r"\bexample\b", r"\buse\b", r"\bapply\b", r"\bimplement\b"],
            QuestionType.ANALYSIS: [r"\banalyze\b", r"\bevaluate\b", r"\bpros\b", r"\bcons\b"],
            QuestionType.TROUBLESHOOTING: [r"\bproblem\b", r"\berror\b", r"\bfix\b", r"\bnot working\b"],
            QuestionType.GREETING: [r"^(hi|hello|hey)\b", r"\bhow are you\b"],
            QuestionType.OUT_OF_SCOPE_GENERAL: [
                # Original patterns
                r"\bweather\b", r"\bjoke\b", r"\bcapital of\b", r"\bwho is\b",
                # Food/Drink related
                r"\bfood\b", r"\beat\b", r"\blunch\b", r"\bdinner\b", r"\bbreakfast\b", r"\brestaurant\b", 
                r"\bcoffee\b", r"\btea\b", r"\bdrink\b", r"\bmeal\b", r"\bcook\b", r"\brecipe\b",
                # Entertainment
                r"\bmovie\b", r"\bfilm\b", r"\bmusic\b", r"\bsong\b", r"\bgame\b(?!.*\bdesign\b)", r"\bsport\b",
                # General non-tech topics
                r"\btravel\b", r"\bvacation\b", r"\bholiday\b", r"\bhealth\b", r"\bmedical\b",
                r"\bpolitics\b", r"\breligion\b", r"\bhistory\b(?!.*\bsoftware\b)", 
                r"\bgeography\b", r"\bmath\b(?!.*\balgorithm\b)",
                # Shopping/Fashion
                r"\bshopping\b", r"\bfashion\b", r"\bclothes\b", r"\bshoes\b",
                # Animals/Nature
                r"\banimal\b", r"\bpet\b", r"\bdog\b", r"\bcat\b", r"\bplant\b", r"\bflower\b"
            ]
        }

        # 🔹 Topic detection keywords
        self.topic_keywords = {
            SoftwareDesignTopic.DESIGN_PATTERNS: [
                "pattern", "singleton", "factory", "strategy", "decorator",
                "observer", "builder", "adapter", "facade", "prototype", "command"
            ],
            SoftwareDesignTopic.SOLID_PRINCIPLES: [
                "solid", "single responsibility", "open closed", "liskov",
                "interface segregation", "dependency inversion"
            ],
            SoftwareDesignTopic.ARCHITECTURE: [
                "architecture", "mvc", "microservices", "monolith", "layered",
                "hexagonal", "clean architecture"
            ],
            SoftwareDesignTopic.DDD: [
                "ddd", "domain driven", "aggregate", "value object", "entity", "repository"
            ],
            SoftwareDesignTopic.QUALITY: [
                "quality", "scalability", "maintainability", "performance", 
                "readability", "refactor"
            ],
            SoftwareDesignTopic.CODE_STRUCTURE: [
                "structure", "class", "function", "module", "interface", "coupling", "cohesion"
            ]
        }

        # 🔥 CRITICAL PATCH — Match EXACT Neo4j Labels
        self.topic_label_map = {
            SoftwareDesignTopic.DESIGN_PATTERNS: [
                "DesignPattern", "design_pattern", "design_patterns", "DesignTool", "AntiPattern", "anti_pattern"
            ],
            SoftwareDesignTopic.SOLID_PRINCIPLES: [
                "solid_principle", "DesignPrinciple", "design_principle", "solide_principle", "SoftwarePrinciple"
            ],
            SoftwareDesignTopic.ARCHITECTURE: [
                "Architecture", "architecture", "ArchPattern", "ArchitecturalPattern"
            ],
            SoftwareDesignTopic.DDD: [
                "DDD", "DDDConcept", "DDDconcept", "DomainDrivenDesign", "domain_driven_design", "Entity", "entity"
            ],
            SoftwareDesignTopic.QUALITY: [
                "Quality", "quality", "QualityAttribute"
            ],
            SoftwareDesignTopic.CODE_STRUCTURE: [
                "CodeStructure", "code_structure", "Interface", "interface", "DataStructure"
            ],
            SoftwareDesignTopic.GENERAL: []
        }

    # ---------------- Main logic ----------------

    def classify_intent(self, user_query: str, graphrag_results: Optional[Dict] = None) -> Dict:
        query = user_query.lower().strip()

        # Check greetings first
        for pattern in self.question_patterns[QuestionType.GREETING]:
            if re.search(pattern, query):
                return self._make_result(QuestionType.GREETING, SoftwareDesignTopic.GENERAL, 1.0, 1.0)

        # Check explicit out-of-scope patterns
        for pattern in self.question_patterns[QuestionType.OUT_OF_SCOPE_GENERAL]:
            if re.search(pattern, query):
                return self._make_result(QuestionType.OUT_OF_SCOPE_GENERAL, SoftwareDesignTopic.GENERAL, 1.0, 1.0)

        # Classify question type and topic
        q_type, q_conf = self._classify_question_type(query)
        topic, t_conf, keywords = self._classify_topic(query)

        # If no software design keywords found AND topic confidence is low, mark as out-of-scope
        if not keywords and t_conf < 0.3 and topic == SoftwareDesignTopic.GENERAL:
            logger.info(f"No software design keywords found in query: '{user_query}' - marking as out-of-scope")
            return self._make_result(QuestionType.OUT_OF_SCOPE_GENERAL, SoftwareDesignTopic.GENERAL, 0.9, 0.9)

        overall_conf = (q_conf + t_conf) / 2
        return self._make_result(q_type, topic, q_conf, t_conf, keywords, overall_conf)

    def _classify_question_type(self, query: str):
        scores = {
            qt: sum(bool(re.search(p, query)) for p in pats)
            for qt, pats in self.question_patterns.items()
            if qt not in [QuestionType.GREETING, QuestionType.OUT_OF_SCOPE_GENERAL]
        }
        if not any(scores.values()):
            return QuestionType.EXPLANATION, 0.3
        best = max(scores, key=scores.get)
        conf = min(0.4 + 0.1 * scores[best], 1.0)
        return best, conf

    def _classify_topic(self, query: str):
        found = {}
        for topic, kws in self.topic_keywords.items():
            matched = [kw for kw in kws if re.search(rf"\b{re.escape(kw)}\b", query)]
            if matched:
                found[topic] = matched
        if not found:
            return SoftwareDesignTopic.GENERAL, 0.2, []
        top_topic = max(found, key=lambda t: len(found[t]))
        conf = min(0.4 + 0.1 * len(found[top_topic]), 0.9)
        return top_topic, conf, found[top_topic]

    def _make_result(self, q_type, topic, q_conf, t_conf, keywords=None, overall=None):
        return {
            "question_type": q_type.value,
            "topic": topic.value,
            "question_confidence": q_conf,
            "topic_confidence": t_conf,
            "keywords_found": keywords or [],
            "overall_confidence": overall or (q_conf + t_conf) / 2,
            "topic_filter_labels": self.topic_label_map.get(topic, [])
        }

    def get_search_parameters(self, user_query, intent: Dict):
        labels = intent.get("topic_filter_labels", [])
        return {
            "user_query_text": user_query,
            "question_type": intent["question_type"],
            "topic_filter_labels": labels,
            "search_depth": 2 if intent["question_type"] == "explanation" else 3,
            "relationship_types": ["RELATES_TO", "USES", "IMPLEMENTS"],
            "min_relevance_score": 0.7,
            "keywords": intent.get("keywords_found", []),
            "extracted_concepts": intent.get("keywords_found", [])
        }