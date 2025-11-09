# intent_classifier.py (improved)
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
        self.question_patterns = {
            QuestionType.EXPLANATION: [r"\bwhat is\b", r"\bexplain\b", r"\bdefine\b", r"\bdescribe\b", r"\bhow does\b"],
            QuestionType.COMPARISON: [r"\bdifference\b", r"\bcompare\b", r"\bvs\b", r"\bversus\b"],
            QuestionType.APPLICATION: [r"\bhow to\b", r"\bexample\b", r"\buse\b", r"\bapply\b", r"\bimplement\b"],
            QuestionType.ANALYSIS: [r"\banalyze\b", r"\bevaluate\b", r"\bpros\b", r"\bcons\b"],
            QuestionType.TROUBLESHOOTING: [r"\bproblem\b", r"\berror\b", r"\bfix\b", r"\bnot working\b"],
            QuestionType.GREETING: [r"^(hi|hello|hey)\b", r"\bhow are you\b"],
            QuestionType.OUT_OF_SCOPE_GENERAL: [r"\bweather\b", r"\bjoke\b", r"\bcapital of\b", r"\bwho is\b"]
        }

        self.topic_keywords = {
            SoftwareDesignTopic.DESIGN_PATTERNS: [
                "pattern", "singleton", "factory", "observer", "strategy", "decorator",
                "builder", "adapter", "facade", "prototype", "command", "state"
            ],
            SoftwareDesignTopic.SOLID_PRINCIPLES: [
                "solid", "single responsibility", "open closed", "liskov", "interface segregation", "dependency inversion"
            ],
            SoftwareDesignTopic.ARCHITECTURE: [
                "architecture", "mvc", "microservices", "monolith", "layered", "hexagonal", "clean architecture"
            ],
            SoftwareDesignTopic.DDD: [
                "domain driven design", "ddd", "aggregate", "entity", "value object", "repository", "bounded context"
            ],
            SoftwareDesignTopic.QUALITY: [
                "quality", "maintainability", "scalability", "performance", "readability", "technical debt", "refactor"
            ],
            SoftwareDesignTopic.CODE_STRUCTURE: [
                "structure", "class", "function", "module", "coupling", "cohesion", "encapsulation", "abstraction"
            ]
        }

        self.topic_label_map = {
            SoftwareDesignTopic.DESIGN_PATTERNS: ['DesignPattern', 'DesignPatternDomain'],
            SoftwareDesignTopic.SOLID_PRINCIPLES: ['DesignPrinciple', 'DesignPrincipleDomain'],
            SoftwareDesignTopic.ARCHITECTURE: ['ArchPattern', 'ArchitecturePattern'],
            SoftwareDesignTopic.DDD: ['DDDConcept', 'DomainDrivenDesign'],
            SoftwareDesignTopic.QUALITY: ['QualityAttribute', 'QualityAttributeDomain'],
            SoftwareDesignTopic.CODE_STRUCTURE: ['CodeStructure', 'CodeStructureDomain'],
            SoftwareDesignTopic.GENERAL: []  # <-- Default to no restriction, not heartbeat nodes
        }

    # --- Main classification logic ---
    def classify_intent(self, user_query: str, graphrag_results: Optional[Dict] = None) -> Dict:
        query = user_query.lower().strip()

        # 1️⃣ Greeting check
        for pattern in self.question_patterns[QuestionType.GREETING]:
            if re.search(pattern, query):
                return self._make_result(QuestionType.GREETING, SoftwareDesignTopic.GENERAL, 1.0, 1.0)

        # 2️⃣ Out of scope
        for pattern in self.question_patterns[QuestionType.OUT_OF_SCOPE_GENERAL]:
            if re.search(pattern, query):
                return self._make_result(QuestionType.OUT_OF_SCOPE_GENERAL, SoftwareDesignTopic.GENERAL, 1.0, 1.0)

        # 3️⃣ Detect question type
        question_type, q_conf = self._classify_question_type(query)

        # 4️⃣ Detect topic
        topic, t_conf, keywords = self._classify_topic(query)

        # 5️⃣ Optional refinement from GraphRAG
        if graphrag_results:
            topic, t_conf = self._refine_topic_with_graph_results(topic, t_conf, graphrag_results)

        overall_conf = (q_conf + t_conf) / 2
        return self._make_result(question_type, topic, q_conf, t_conf, keywords, overall_conf)

    # --- Question Type ---
    def _classify_question_type(self, query: str) -> Tuple[QuestionType, float]:
        scores = {qt: sum(bool(re.search(p, query)) for p in pats)
                  for qt, pats in self.question_patterns.items() if qt not in [QuestionType.GREETING, QuestionType.OUT_OF_SCOPE_GENERAL]}
        if not any(scores.values()):
            return QuestionType.EXPLANATION, 0.3
        best = max(scores, key=scores.get)
        conf = min(0.4 + 0.1 * scores[best], 1.0)
        return best, conf

    # --- Topic ---
    def _classify_topic(self, query: str) -> Tuple[SoftwareDesignTopic, float, List[str]]:
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

    # --- Graph refinement (optional) ---
    def _refine_topic_with_graph_results(self, topic: SoftwareDesignTopic, conf: float, results: Dict) -> Tuple[SoftwareDesignTopic, float]:
        if not results or 'results' not in results:
            return topic, conf
        label_counts = {}
        for res in results['results']:
            labels = res.get('labels') or []
            for l in labels:
                for t, mapped_labels in self.topic_label_map.items():
                    if l in mapped_labels:
                        label_counts[t] = label_counts.get(t, 0) + 1
        if not label_counts:
            return topic, conf
        new_topic = max(label_counts, key=label_counts.get)
        if new_topic != topic and label_counts[new_topic] > 1:
            return new_topic, min(conf + 0.2, 0.95)
        return topic, conf

    # --- Utility ---
    def _make_result(self, q_type, topic, q_conf, t_conf, keywords=None, overall=None):
        return {
            'question_type': q_type.value,
            'topic': topic.value,
            'question_confidence': q_conf,
            'topic_confidence': t_conf,
            'keywords_found': keywords or [],
            'overall_confidence': overall or (q_conf + t_conf) / 2
        }

    def get_search_parameters(self, user_query: str, intent: Dict) -> Dict:
        topic = SoftwareDesignTopic(intent['topic'])
        labels = self.topic_label_map.get(topic, [])
        return {
            'user_query_text': user_query,
            'question_type': intent['question_type'],
            'topic_filter_labels': labels,
            'search_depth': 2 if intent['question_type'] == "explanation" else 3,
            'relationship_types': ['RELATES_TO', 'USES', 'IMPLEMENTS'],
            'min_relevance_score': 0.7,
            'keywords': intent['keywords_found'],
            'extracted_concepts': intent['keywords_found']
        }
