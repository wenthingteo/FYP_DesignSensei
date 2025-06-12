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
    # Consider a 'GENERAL' or 'UNCATEGORIZED' type for fallbacks if needed

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
            QuestionType.EXPLANATION: [
                r'\b(?:what|explain|define|describe|tell me about)\b',
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
                'code quality', 'technical debt', 'refactoring', 'clean code'
            ],
            SoftwareDesignTopic.CODE_STRUCTURE: [
                'structure', 'organization', 'module', 'package', 'namespace',
                'class', 'method', 'function', 'coupling', 'cohesion',
                'separation of concerns', 'abstraction', 'encapsulation'
            ]
        }
       
        # Mapping from Neo4j node labels (from your knowledge graph) to internal topic enums
        # IMPORTANT: Only map conceptual labels that represent the topics your chatbot teaches.
        # Ignore generic internal Neo4j labels or import artifacts.
        self.graph_label_to_topic_mapping = {
            # Conceptual Labels from your `CALL db.labels()` output
            'DesignPattern': SoftwareDesignTopic.DESIGN_PATTERNS,
            'DDDConcept': SoftwareDesignTopic.DDD,
            'CodeStructure': SoftwareDesignTopic.CODE_STRUCTURE,
            'ArchPattern': SoftwareDesignTopic.ARCHITECTURE,
            'QualityAttribute': SoftwareDesignTopic.QUALITY,
            'DesignPrinciple': SoftwareDesignTopic.SOLID_PRINCIPLES,
           
            # If 'UnknownLabel' truly represents a topic, map it.
            # For now, mapping it to GENERAL as a safe fallback.
            'UnknownLabel': SoftwareDesignTopic.GENERAL,
            # System/Import-related labels that don't represent conceptual topics, mapped to GENERAL
            'KNOWLEDGE NODE': SoftwareDesignTopic.GENERAL,
            'RELATIONSHIP': SoftwareDesignTopic.GENERAL,
            'NODE': SoftwareDesignTopic.GENERAL,
            'Relationship': SoftwareDesignTopic.GENERAL,
            'Node': SoftwareDesignTopic.GENERAL,
            'node': SoftwareDesignTopic.GENERAL,
            'relationship': SoftwareDesignTopic.GENERAL,
            'Ver3KnowledgeGraphSemanticallyEnhancedDedupedNodeNeo4jCsv': SoftwareDesignTopic.GENERAL,
            'Ver3KnowledgeGraphSemanticallyEnhancedDedupedRelationshipNeo4jCsv': SoftwareDesignTopic.GENERAL,
        }

    def classify_intent(self, user_query: str, graphrag_results: Optional[Dict] = None) -> Dict:
        """
        Classify user query into question type and software design topic.
        Can optionally use GraphRAG results for refinement.

        Args:
            user_query (str): User's question or statement
            graphrag_results (Dict, optional): Results from GraphRAG search.
                                               Expected to contain node information,
                                               potentially with 'label' or 'name' keys.

        Returns:
            Dict: Contains question_type, topic, confidence_score, and keywords_found
                  All Enum values are converted to their string representations.
        """
        query_lower = user_query.lower()

        # Step 1: Classify question type based on user query keywords/patterns
        question_type, question_confidence = self._classify_question_type(query_lower)

        # Step 2: Classify topic based on user query keywords
        topic, topic_confidence, found_keywords = self._classify_topic(query_lower)

        # Step 3: Refine topic classification using GraphRAG results (New/Improved Step)
        if graphrag_results: # Only attempt refinement if graphrag_results are provided
            refined_topic, refined_topic_confidence = self._refine_topic_with_graph_results(
                current_topic=topic,
                current_confidence=topic_confidence,
                graphrag_raw_results_input=graphrag_results # Pass the raw input to the refined handler
            )
            # If refinement yields higher confidence, use it
            if refined_topic_confidence > topic_confidence:
                topic = refined_topic
                topic_confidence = refined_topic_confidence
                logger.info(f"Topic refined by graph results: {topic.value} (Confidence: {topic_confidence:.2f})")

        overall_confidence = (question_confidence + topic_confidence) / 2

        # --- FIX: Convert Enum objects to their string values before returning ---
        return {
            'question_type': question_type.value, # Convert Enum to string
            'topic': topic.value, # Convert Enum to string
            'question_confidence': question_confidence,
            'topic_confidence': topic_confidence,
            'keywords_found': found_keywords,
            'overall_confidence': overall_confidence
        }

    def _classify_question_type(self, query: str) -> Tuple[QuestionType, float]:
        """Classify the type of question being asked based on regex patterns."""
        scores = {}
        # Count keyword matches based on regex patterns
        for q_type, patterns in self.question_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query, re.IGNORECASE))
                score += matches
            scores[q_type] = score

        if not any(scores.values()):
            return QuestionType.EXPLANATION, 0.3

        # Determine best type and its confidence
        total_matches = sum(scores.values())
        best_type = max(scores.items(), key=lambda x: x[1])
       
        # Calculate confidence: scale based on proportion of matches or absolute count
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
        returned by GraphRAG search.
        """
        if not graphrag_raw_results_input:
            return current_topic, current_confidence

        list_of_results = []
        if isinstance(graphrag_raw_results_input, dict):
            if 'results' in graphrag_raw_results_input and isinstance(graphrag_raw_results_input['results'], list):
                list_of_results = graphrag_raw_results_input['results']
            else:
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
            label = result.get('label')
            if label:
                mapped_topic = self.graph_label_to_topic_mapping.get(label)
                if mapped_topic:
                    label_counts[mapped_topic] = label_counts.get(mapped_topic, 0) + 1
                else:
                    logger.debug(f"Graph label '{label}' from search results not found in internal topic mapping.")
            else:
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
        extracted_concepts = []
       
        # --- FIX: Use the string values from intent_result for topic ---
        topic_str = intent_result['topic'] # This is now a string thanks to the fix in classify_intent
       
        # Use the string value to access topic_keywords
        topic_enum = SoftwareDesignTopic(topic_str) # Convert back to Enum for internal logic if needed
       
        if topic_enum in self.topic_keywords:
            for keyword in self.topic_keywords[topic_enum]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', user_query.lower()):
                    extracted_concepts.append(keyword)

        extracted_concepts = list(set(extracted_concepts))

        return {
            'user_query_text': user_query,
            'question_type': intent_result['question_type'], # This is now a string
            'topic_filter_labels': self._topic_to_label_filter(topic_enum), # Pass the Enum back if _topic_to_label_filter expects it
            'search_depth': self._get_search_depth(QuestionType(intent_result['question_type'])), # Convert back to Enum
            'relationship_types': self._get_relevant_relationships(QuestionType(intent_result['question_type'])), # Convert back to Enum
            'min_relevance_score': 0.7,
            'keywords': intent_result['keywords_found'],
            'extracted_concepts': extracted_concepts
        }

    def _topic_to_label_filter(self, topic: SoftwareDesignTopic) -> List[str]:
        """Map software design topics to Neo4j node labels that the search module will use for filtering."""
        mapping = {
            SoftwareDesignTopic.DESIGN_PATTERNS: ['DesignPattern', 'Pattern'],
            SoftwareDesignTopic.SOLID_PRINCIPLES: ['DesignPrinciple', 'Principle'],
            SoftwareDesignTopic.ARCHITECTURE: ['Architecture', 'ArchitecturalPattern', 'ArchitecturalComponent', 'ArchPattern'],
            SoftwareDesignTopic.DDD: ['DomainConcept', 'DDDConcept'],
            SoftwareDesignTopic.QUALITY: ['QualityAttribute', 'QualityMetric', 'CodeQuality'],
            SoftwareDesignTopic.CODE_STRUCTURE: ['CodeStructure', 'OrganizationPrinciple'],
            SoftwareDesignTopic.GENERAL: ['Paradigm', 'UnknownLabel', 'KNOWLEDGE NODE', 'RELATIONSHIP', 'NODE', 'Relationship', 'Node', 'node', 'relationship', 'Ver3KnowledgeGraphSemanticallyEnhancedDedupedNodeNeo4jCsv', 'Ver3KnowledgeGraphSemanticallyEnhancedDedupedRelationshipNeo4jCsv'] # Included all generic/import labels
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


# Example usage and testing (updated)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    classifier = IntentClassifier()

    # Mock GraphRAG results for testing refinement
    mock_graph_results_srp_list_format = {
        'results': [
            {'id': 'n_a3d57b', 'name': 'Single Responsibility Principle', 'label': 'DesignPrinciple', 'relevance_score': 0.9},
            {'id': 'n_xyz', 'name': 'Cohesion', 'label': 'CodeQuality', 'relevance_score': 0.8},
        ]
    }
   
    mock_graph_results_srp_dict_format = {
        "Single Responsibility Principle": {
            "node_id": "n_a3d57b",
            "name": "Single Responsibility Principle",
            "label": "DesignPrinciple",
            "description": "A class should have only one reason to change.",
            "source": "solid-principles.pdf",
            "page": 5,
            "relevance_score": 0.9
        },
        "Cohesion": {
            "node_id": "n_xyz",
            "name": "Cohesion",
            "label": "CodeQuality",
            "description": "Degree to which elements within a module belong together.",
            "relevance_score": 0.8
        }
    }

    mock_graph_results_architecture = {
        'results': [
            {'id': 'n_599c9c5', 'name': 'Microservices Architecture', 'label': 'Architecture', 'relevance_score': 0.9},
            {'id': 'n_f4g5h6', 'name': 'API Gateway', 'label': 'ArchitecturalComponent', 'relevance_score': 0.85},
        ]
    }
    mock_graph_results_general = {
        'results': [
            {'id': 'n_jkl', 'name': 'Object-Oriented Programming', 'label': 'Paradigm', 'relevance_score': 0.7},
        ]
    }
    mock_graph_results_parser = {
        'results': [
            {'id': 'n_9a83ab', 'name': 'Parser', 'label': 'CodeStructure', 'description': 'A component of the compiler', 'relevance_score': 0.9},
        ]
    }


    test_cases = [
        ("What is the Single Responsibility Principle?", mock_graph_results_srp_list_format),
        ("Explain the SRP.", mock_graph_results_srp_dict_format),
        ("Compare MVC and MVVM architectures.", mock_graph_results_architecture),
        ("How to implement a Factory Method pattern?", mock_graph_results_srp_list_format),
        ("Is this system design scalable?", mock_graph_results_architecture),
        ("Why is my code violating dependency inversion principle?", mock_graph_results_srp_list_format),
        ("Tell me about software testing.", mock_graph_results_general),
        ("What is a Parser?", mock_graph_results_parser)
    ]

    print("--- Intent Classifier Testing ---")
    for query_text, graph_results in test_cases:
        print(f"\nQuery: '{query_text}'")
        intent_result = classifier.classify_intent(user_query=query_text, graphrag_results=graph_results)
        search_params = classifier.get_search_parameters(user_query=query_text, intent_result=intent_result)

        print(f"  Question Type: {intent_result['question_type']} (Conf: {intent_result['question_confidence']:.2f})")
        print(f"  Topic: {intent_result['topic']} (Conf: {intent_result['topic_confidence']:.2f})")
        print(f"  Overall Confidence: {intent_result['overall_confidence']:.2f}")
        print(f"  Keywords Found (from query): {intent_result['keywords_found']}")
        print(f"  Search Parameters for Search Module:")
        for key, value in search_params.items():
            if key != 'user_query_text':
                print(f"    - {key}: {value}")