# prompt_engine/intent_classifier.py
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
    # Added new question types for chatbot behavior control
    GREETING = "greeting"
    OUT_OF_SCOPE_GENERAL = "out_of_scope_general"
    UNKNOWN = "unknown" # General fallback for software design, if no specific type matched

class SoftwareDesignTopic(Enum):
    DESIGN_PATTERNS = "design_patterns"
    SOLID_PRINCIPLES = "solid_principles"
    ARCHITECTURE = "architecture"
    DDD = "ddd"
    QUALITY = "quality"
    CODE_STRUCTURE = "code_structure"
    GENERAL = "general_software_design" # Added for broader queries or when topic is unclear

class IntentClassifier:
    def __init__(self):
        # Regular expression patterns to identify question types
        self.question_patterns = {
            # Existing software design question types
            QuestionType.EXPLANATION: [
                r'\b(?:what is|what\'s|explain|define|describe|tell me about)\b',
                r'\bis\s+(?:the|a)\b',
                r'\bhow does\b',
                r'\bmeaning of\b'
            ],
            QuestionType.COMPARISON: [
                r'\b(?:difference|compare|vs|versus|between)\b',
                r'\bbetter\s+(?:than|or)\b',
                r'\bwhich\s+(?:is|should)\b',
                r'\badvantages?\s+(?:of|and)\s+disadvantages?\b'
            ],
            QuestionType.APPLICATION: [
                r'\bhow\s+(?:to|can|do)\b',
                r'\bimplement(?:ation)?\b',
                r'\bexample\s+(?:of|code)\b',
                r'\buse\s+(?:case|in)\b',
                r'\bapply\b'
            ],
            QuestionType.ANALYSIS: [
                r'\b(?:evaluate|analyze|assess|review)\b',
                r'\bis\s+(?:this|it)\s+(?:good|bad|correct)\b',
                r'\bpros\s+and\s+cons\b',
                r'\bwhy\s+(?:is|should|would)\b'
            ],
            QuestionType.TROUBLESHOOTING: [
                r'\b(?:problem|issue|error|wrong|fix|debug)\b',
                r'\bnot\s+working\b',
                r'\bviolat(?:e|ing)\b',
                r'\bbad\s+(?:practice|design)\b'
            ],
            # New greeting and general out-of-scope patterns
            QuestionType.GREETING: [
                r"^(hi|hello|hey)\b", # Starts with hi/hello/hey
                r"\b(good morning|good afternoon|good evening|how are you|how's it going|what's up)\b"
            ],
            QuestionType.OUT_OF_SCOPE_GENERAL: [
                r"\b(weather|joke|capital of|who is|what time is it|what's your name|how old are you|random fact|meaning of life)\b",
                r"\b(can you tell me about yourself|what can you do|can you help me with that)\b" # More general requests
            ]
        }
       
        # Keywords to identify software design topics
        self.topic_keywords = {
            SoftwareDesignTopic.DESIGN_PATTERNS: [
                'pattern', 'singleton', 'factory', 'observer', 'strategy', 'decorator',
                'adapter', 'facade', 'builder', 'prototype', 'command', 'state',
                'template method', 'visitor', 'chain of responsibility', 'mediator',
                'memento', 'flyweight', 'proxy', 'bridge', 'composite', 'iterator'
            ],
            SoftwareDesignTopic.SOLID_PRINCIPLES: [
                'solid', 'single responsibility', 'open closed', 'liskov substitution',
                'interface segregation', 'dependency inversion', 'srp', 'ocp', 'lsp',
                'isp', 'dip', 'responsibility', 'extension', 'substitution', 'segregation'
            ],
            SoftwareDesignTopic.ARCHITECTURE: [
                'architecture', 'microservices', 'monolith', 'mvc', 'mvp', 'mvvm',
                'layered', 'hexagonal', 'clean architecture', 'onion', 'component',
                'service', 'api', 'rest', 'graphql', 'event driven', 'cqrs'
            ],
            SoftwareDesignTopic.DDD: [
                'domain driven design', 'ddd', 'aggregate', 'entity', 'value object',
                'repository', 'service', 'factory', 'domain model', 'bounded context',
                'ubiquitous language', 'domain event', 'specification'
            ],
            SoftwareDesignTopic.QUALITY: [
                'quality', 'maintainability', 'testability', 'readability',
                'performance', 'scalability', 'reliability', 'usability',
                'code quality', 'technical debt', 'refactoring', 'clean code',
                'coupling', 'cohesion'  # Added these as they're likely to exist
            ],
            SoftwareDesignTopic.CODE_STRUCTURE: [
                'structure', 'organization', 'module', 'package', 'namespace',
                'class', 'method', 'function', 'coupling', 'cohesion',
                'separation of concerns', 'abstraction', 'encapsulation'
            ]
        }
       
        # Mapping from Neo4j node labels (from your knowledge graph) to internal topic enums
        self.graph_label_to_topic_mapping = {
            'DesignPattern': SoftwareDesignTopic.DESIGN_PATTERNS,
            'DesignPatternDomain': SoftwareDesignTopic.DESIGN_PATTERNS,
            'DesignPatternsTopic': SoftwareDesignTopic.DESIGN_PATTERNS,
            'DDDConcept': SoftwareDesignTopic.DDD,
            'DomainDrivenDesign': SoftwareDesignTopic.DDD,
            'CodeStructure': SoftwareDesignTopic.CODE_STRUCTURE,
            'CodeStructureDomain': SoftwareDesignTopic.CODE_STRUCTURE,
            'ArchPattern': SoftwareDesignTopic.ARCHITECTURE,
            'ArchPatternDomain': SoftwareDesignTopic.ARCHITECTURE,
            'ArchitecturePattern': SoftwareDesignTopic.ARCHITECTURE,
            'QualityAttribute': SoftwareDesignTopic.QUALITY,
            'QualityAttributeDomain': SoftwareDesignTopic.QUALITY,
            'DesignPrinciple': SoftwareDesignTopic.SOLID_PRINCIPLES,
            'DesignPrincipleDomain': SoftwareDesignTopic.SOLID_PRINCIPLES,
        }

        # Keywords that indicate *any* software design relevance
        self.any_software_design_keywords = [
            kw for sublist in self.topic_keywords.values() for kw in sublist
        ] + ['software', 'design', 'programming', 'developer', 'codebase', 'application', 'system']


    def classify_intent(self, user_query: str, graphrag_results: Optional[Dict] = None) -> Dict:
        """
        Classify user query into question type and software design topic.
        Prioritizes greeting and out-of-scope, then specific software design intents.
        """
        query_lower = user_query.lower()

        # 1. Highest Priority: Greetings
        for pattern in self.question_patterns[QuestionType.GREETING]:
            if re.search(pattern, query_lower):
                return {
                    'question_type': QuestionType.GREETING.value,
                    'topic': SoftwareDesignTopic.GENERAL.value,
                    'question_confidence': 1.0,
                    'topic_confidence': 1.0,
                    'keywords_found': [],
                    'overall_confidence': 1.0
                }
        
        # 2. Second Priority: General Out-of-Scope (if no software design keywords detected)
        # Check if the query contains any software design related keywords
        is_software_design_query = any(re.search(r'\b' + re.escape(kw) + r'\b', query_lower) for kw in self.any_software_design_keywords)

        for pattern in self.question_patterns[QuestionType.OUT_OF_SCOPE_GENERAL]:
            if re.search(pattern, query_lower) and not is_software_design_query:
                return {
                    'question_type': QuestionType.OUT_OF_SCOPE_GENERAL.value,
                    'topic': SoftwareDesignTopic.GENERAL.value,
                    'question_confidence': 1.0,
                    'topic_confidence': 1.0,
                    'keywords_found': [],
                    'overall_confidence': 1.0
                }

        # 3. Third Priority: Software Design Specific Intents
        question_type, question_confidence = self._classify_question_type_sd(query_lower) # Use a helper for SD types
        topic, topic_confidence, found_keywords = self._classify_topic(query_lower)

        # Refine topic classification using GraphRAG results (if provided and relevant)
        if graphrag_results:
            refined_topic, refined_topic_confidence = self._refine_topic_with_graph_results(
                current_topic=SoftwareDesignTopic(topic), # Pass Enum
                current_confidence=topic_confidence,
                graphrag_raw_results_input=graphrag_results
            )
            if refined_topic_confidence > topic_confidence:
                topic = refined_topic.value # Store as string
                topic_confidence = refined_topic_confidence
                logger.info(f"Topic refined by graph results: {topic} (Confidence: {topic_confidence:.2f})")
        
        overall_confidence = (question_confidence + topic_confidence) / 2

        # Final check: If it was classified as OUT_OF_SCOPE_GENERAL initially (e.g. from keyword list)
        # but somehow has high SD confidence, we should consider it SD.
        if question_type == QuestionType.OUT_OF_SCOPE_GENERAL and overall_confidence < 0.5:
             # If it was caught by generic out-of-scope but *no* SD keywords, keep it OOS.
             # If it has SD keywords, default to explanation.
             return {
                'question_type': QuestionType.OUT_OF_SCOPE_GENERAL.value,
                'topic': SoftwareDesignTopic.GENERAL.value,
                'question_confidence': question_confidence,
                'topic_confidence': topic_confidence,
                'keywords_found': found_keywords,
                'overall_confidence': overall_confidence
            }
        
        # Default to explanation if it seems SD-related but no specific question type pattern matched well
        if question_type == QuestionType.UNKNOWN and is_software_design_query:
            question_type = QuestionType.EXPLANATION
            question_confidence = max(question_confidence, 0.4) # Give it a base confidence

        return {
            'question_type': question_type.value,
            'topic': topic if isinstance(topic, str) else topic.value, # Ensure it's string
            'question_confidence': question_confidence,
            'topic_confidence': topic_confidence,
            'keywords_found': found_keywords,
            'overall_confidence': overall_confidence
        }

    def _classify_question_type_sd(self, query: str) -> Tuple[QuestionType, float]:
        """Classify the type of software design question being asked based on regex patterns."""
        scores = {}
        # Iterate only over software design-specific question types
        for q_type in [
            QuestionType.EXPLANATION, QuestionType.COMPARISON,
            QuestionType.APPLICATION, QuestionType.ANALYSIS, QuestionType.TROUBLESHOOTING
        ]:
            score = 0
            for pattern in self.question_patterns[q_type]:
                matches = len(re.findall(pattern, query, re.IGNORECASE))
                score += matches
            scores[q_type] = score

        if not any(scores.values()):
            # If no specific SD pattern matched, but it has SD keywords (handled in main classify_intent)
            # then it defaults to UNKNOWN, which can be re-assigned to EXPLANATION later.
            return QuestionType.UNKNOWN, 0.3

        total_matches = sum(scores.values())
        best_type = max(scores.items(), key=lambda x: x[1])
       
        confidence = min(best_type[1] / total_matches if total_matches > 0 else 0.3, 1.0)
        if best_type[1] > 0 and confidence < 0.5:
             confidence = 0.5

        return best_type[0], confidence

    def _classify_topic(self, query: str) -> Tuple[SoftwareDesignTopic, float, List[str]]:
        """Classify the software design topic being discussed using predefined keywords."""
        topic_scores = {}
        found_keywords_per_topic = {}

        for topic, keywords in self.topic_keywords.items():
            score = 0
            current_topic_keywords = []
           
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', query, re.IGNORECASE):
                    score += 1
                    current_topic_keywords.append(keyword)
           
            topic_scores[topic] = score
            found_keywords_per_topic[topic] = current_topic_keywords

        if not any(topic_scores.values()):
            return SoftwareDesignTopic.GENERAL, 0.2, []

        best_topic = max(topic_scores.items(), key=lambda x: x[1])
       
        max_possible_keywords = len(self.topic_keywords.get(best_topic[0], [1]))
        confidence = min(best_topic[1] / max_possible_keywords if max_possible_keywords > 0 else 0.2, 1.0)
       
        if best_topic[1] > 0 and confidence < 0.4:
            confidence = 0.4

        return best_topic[0], confidence, found_keywords_per_topic.get(best_topic[0], [])

    def _refine_topic_with_graph_results(self, current_topic: SoftwareDesignTopic,
                                        current_confidence: float,
                                        graphrag_raw_results_input: Dict) -> Tuple[SoftwareDesignTopic, float]:
        """
        Refine topic classification by inspecting the labels (and potentially names) of the nodes
        returned by GraphRAG search. Now handles Neo4j Node objects properly.
        """
        if not graphrag_raw_results_input:
            return current_topic, current_confidence

        list_of_results = []
        if isinstance(graphrag_raw_results_input, dict):
            if 'results' in graphrag_raw_results_input and isinstance(graphrag_raw_results_input['results'], list):
                list_of_results = graphrag_raw_results_input['results']
            else:
                # If it's a dict but not the expected 'results' key, try iterating values
                list_of_results = list(graphrag_raw_results_input.values()) 
        elif isinstance(graphrag_raw_results_input, list):
            list_of_results = graphrag_raw_results_input
        else:
            logger.warning(f"Unexpected graphrag_results_input format: {type(graphrag_raw_results_input)}. Expected dict or list.")
            return current_topic, current_confidence

        if not list_of_results:
            return current_topic, current_confidence

        label_counts = {}
        for result in list_of_results:
            # Handle Neo4j Node objects by converting to dict
            if hasattr(result, 'labels') and hasattr(result, 'get'):
                # This is a Neo4j Node object
                result_dict = dict(result)
                labels_list = list(result.labels)
                result_dict['_labels_'] = labels_list
                result = result_dict
            
            label_or_labels = result.get('label') or result.get('_labels_') or result.get('labels')
            
            if isinstance(label_or_labels, list):
                # If it's a list of labels, iterate through them
                for label in label_or_labels:
                    mapped_topic = self.graph_label_to_topic_mapping.get(label)
                    if mapped_topic:
                        label_counts[mapped_topic] = label_counts.get(mapped_topic, 0) + 1
                    else:
                        logger.debug(f"Graph label '{label}' from search results not found in internal topic mapping.")
            elif isinstance(label_or_labels, str):
                # If it's a single label string
                mapped_topic = self.graph_label_to_topic_mapping.get(label_or_labels)
                if mapped_topic:
                    label_counts[mapped_topic] = label_counts.get(mapped_topic, 0) + 1
                else:
                    logger.debug(f"Graph label '{label_or_labels}' from search results not found in internal topic mapping.")
            else:
                # Fallback to checking 'name' if no label is found
                name_ = result.get('name')
                if name_:
                    for topic_enum, keywords in self.topic_keywords.items():
                        if any(re.search(r'\b' + re.escape(kw) + r'\b', name_.lower(), re.IGNORECASE) for kw in keywords):
                            label_counts[topic_enum] = label_counts.get(topic_enum, 0) + 0.5
                            logger.debug(f"Inferred topic '{topic_enum.value}' for result name '{name_}' (missing label).")
                            break

        if not any(label_counts.values()):
            return current_topic, current_confidence

        most_frequent_topic, count = max(label_counts.items(), key=lambda item: item[1])

        new_confidence_boost = min(count * 0.05, 0.2)
        new_confidence = current_confidence + new_confidence_boost
        new_confidence = min(new_confidence, 0.95)

        if most_frequent_topic != current_topic and new_confidence > current_confidence + 0.1:
            logger.info(f"Topic refined from {current_topic.value} to {most_frequent_topic.value} by graph results (Conf: {new_confidence:.2f})")
            return most_frequent_topic, new_confidence
        elif most_frequent_topic == current_topic and new_confidence > current_confidence:
            logger.info(f"Confidence for {current_topic.value} boosted by graph results to {new_confidence:.2f}")
            return current_topic, new_confidence
    
        return current_topic, current_confidence

    def get_search_parameters(self, user_query: str, intent_result: Dict) -> Dict:
        """
        Convert intent classification and user query to search parameters for GraphRAG.
        This method compiles parameters that the search module will use.
        """
        # If the intent is not a software design intent, return empty search parameters.
        if intent_result['question_type'] in [QuestionType.GREETING.value, QuestionType.OUT_OF_SCOPE_GENERAL.value]:
            return {}

        extracted_concepts = []
        topic_str = intent_result['topic']
        topic_enum = SoftwareDesignTopic(topic_str) # Convert back to Enum for internal logic

        if topic_enum in self.topic_keywords:
            for keyword in self.topic_keywords[topic_enum]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', user_query.lower()):
                    extracted_concepts.append(keyword)

        extracted_concepts = list(set(extracted_concepts))

        return {
            'user_query_text': user_query,
            'question_type': intent_result['question_type'],
            'topic_filter_labels': self._topic_to_label_filter(topic_enum),
            'search_depth': self._get_search_depth(QuestionType(intent_result['question_type'])),
            'relationship_types': self._get_relevant_relationships(QuestionType(intent_result['question_type'])),
            'min_relevance_score': 0.7,
            'keywords': intent_result['keywords_found'],
            'extracted_concepts': extracted_concepts
        }


    def _topic_to_label_filter(self, topic: SoftwareDesignTopic) -> List[str]:
        """Map software design topics to Neo4j node labels that the search module will use for filtering."""
        mapping = {
            SoftwareDesignTopic.DESIGN_PATTERNS: ['DesignPattern', 'DesignPatternDomain', 'DesignPatternsTopic'],
            SoftwareDesignTopic.SOLID_PRINCIPLES: ['DesignPrinciple', 'DesignPrincipleDomain'],
            SoftwareDesignTopic.ARCHITECTURE: ['ArchPattern', 'ArchPatternDomain', 'ArchitecturePattern'],
            SoftwareDesignTopic.DDD: ['DDDConcept', 'DomainDrivenDesign'],
            SoftwareDesignTopic.QUALITY: ['QualityAttribute', 'QualityAttributeDomain'],
            SoftwareDesignTopic.CODE_STRUCTURE: ['CodeStructure', 'CodeStructureDomain'],
            SoftwareDesignTopic.GENERAL: ['KNOWLEDGE NODE', 'NODE', 'Node', 'RELATIONSHIP', 'Heartbeat']
        }
        return mapping.get(topic, [])

    def _get_search_depth(self, question_type: QuestionType) -> int:
        """Determine how deep to search in the graph based on question type."""
        depth_mapping = {
            QuestionType.EXPLANATION: 2,
            QuestionType.COMPARISON: 3,
            QuestionType.APPLICATION: 2,
            QuestionType.ANALYSIS: 3,
            QuestionType.TROUBLESHOOTING: 2
        }
        return depth_mapping.get(question_type, 2)

    def _get_relevant_relationships(self, question_type: QuestionType) -> List[str]:
        """Get relevant relationship types to traverse based on question type."""
        relationship_mapping = {
            QuestionType.EXPLANATION: ['CONTAINS', 'RELATES_TO', 'HAS_PROPERTY', 'DEFINES'],
            QuestionType.COMPARISON: ['SIMILAR_TO', 'DIFFERS_FROM', 'RELATES_TO', 'COMPARED_WITH', 'CONTRASTS_WITH'],
            QuestionType.APPLICATION: ['IMPLEMENTS', 'USES', 'APPLIES_TO', 'EXAMPLE_OF', 'DEPENDS_ON'],
            QuestionType.ANALYSIS: ['AFFECTS', 'RELATES_TO', 'CAUSES', 'EVALUATES', 'HAS_IMPLICATION', 'VIOLATES'],
            QuestionType.TROUBLESHOOTING: ['VIOLATES', 'CONFLICTS_WITH', 'CAUSES', 'RESOLVES', 'IMPLIES_ISSUE']
        }
        return relationship_mapping.get(question_type, ['RELATES_TO'])

    def validate_database_labels(self, driver):
        """
        Helper method to validate which labels actually exist in the Neo4j database.
        Call this during initialization to filter out non-existent labels.
        """
        try:
            with driver.session() as session:
                result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
                existing_labels = [record["label"] for record in result]
                logger.info(f"Existing database labels: {existing_labels}")
                
                # Update mappings to only include existing labels
                for topic, labels in self._topic_to_label_filter(SoftwareDesignTopic.GENERAL).items():
                    filtered_labels = [label for label in labels if label in existing_labels]
                    if len(filtered_labels) != len(labels):
                        logger.warning(f"Topic {topic}: Removed non-existent labels {set(labels) - set(filtered_labels)}")
                
                return existing_labels
        except Exception as e:
            logger.error(f"Failed to validate database labels: {e}")
            return []
    
# Example usage and testing (updated)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    classifier = IntentClassifier()