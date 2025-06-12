"""
Intent Classifier for Software Design Education Chatbot
"""
import re
from typing import Dict, List, Tuple
from enum import Enum

class QuestionType(Enum):
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    APPLICATION = "application"
    ANALYSIS = "analysis"
    TROUBLESHOOTING = "troubleshooting"

class SoftwareDesignTopic(Enum):
    DESIGN_PATTERNS = "design_patterns"
    SOLID_PRINCIPLES = "solid_principles"
    ARCHITECTURE = "architecture"
    DDD = "ddd"
    QUALITY = "quality"
    CODE_STRUCTURE = "code_structure"

class IntentClassifier:
    def __init__(self):
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

    def classify_intent(self, user_query: str) -> Dict:
        """
        Classify user query into question type and software design topic
        
        Args:
            user_query (str): User's question or statement
            
        Returns:
            Dict: Contains question_type, topic, confidence_score, and keywords_found
        """
        query_lower = user_query.lower()
        
        # Classify question type
        question_type, question_confidence = self._classify_question_type(query_lower)
        
        # Classify topic
        topic, topic_confidence, found_keywords = self._classify_topic(query_lower)
        
        return {
            'question_type': question_type,
            'topic': topic,
            'question_confidence': question_confidence,
            'topic_confidence': topic_confidence,
            'keywords_found': found_keywords,
            'overall_confidence': (question_confidence + topic_confidence) / 2
        }

    def _classify_question_type(self, query: str) -> Tuple[QuestionType, float]:
        """Classify the type of question being asked"""
        scores = {}
        
        for q_type, patterns in self.question_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query, re.IGNORECASE))
                score += matches
            scores[q_type] = score
        
        if not any(scores.values()):
            return QuestionType.EXPLANATION, 0.3  # Default with low confidence
            
        best_type = max(scores.items(), key=lambda x: x[1])
        confidence = min(best_type[1] * 0.3, 1.0)  # Scale confidence
        
        return best_type[0], confidence

    def _classify_topic(self, query: str) -> Tuple[SoftwareDesignTopic, float, List[str]]:
        """Classify the software design topic being discussed"""
        topic_scores = {}
        found_keywords = {}
        
        for topic, keywords in self.topic_keywords.items():
            score = 0
            topic_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in query:
                    score += 1
                    topic_keywords.append(keyword)
            
            topic_scores[topic] = score
            found_keywords[topic] = topic_keywords
        
        if not any(topic_scores.values()):
            return SoftwareDesignTopic.DESIGN_PATTERNS, 0.2, []  # Default with low confidence
            
        best_topic = max(topic_scores.items(), key=lambda x: x[1])
        confidence = min(best_topic[1] * 0.2, 1.0)  # Scale confidence
        
        return best_topic[0], confidence, found_keywords[best_topic[0]]

    def get_search_parameters(self, intent_result: Dict) -> Dict:
        """
        Convert intent classification to search parameters for GraphRAG
        
        Args:
            intent_result (Dict): Result from classify_intent method
            
        Returns:
            Dict: Parameters for GraphRAG search
        """
        return {
            'semantic_type': 'concept',  # Based on your CSV structure
            'label_filter': self._topic_to_label_filter(intent_result['topic']),
            'search_depth': self._get_search_depth(intent_result['question_type']),
            'relationship_types': self._get_relevant_relationships(intent_result['question_type']),
            'min_relevance_score': 0.7,
            'keywords': intent_result['keywords_found']
        }

    def _topic_to_label_filter(self, topic: SoftwareDesignTopic) -> List[str]:
        """Map software design topics to Neo4j node labels"""
        mapping = {
            SoftwareDesignTopic.DESIGN_PATTERNS: ['DesignPattern', 'Pattern'],
            SoftwareDesignTopic.SOLID_PRINCIPLES: ['DesignPrinciple', 'Principle'],
            SoftwareDesignTopic.ARCHITECTURE: ['Architecture', 'ArchitecturalPattern'],
            SoftwareDesignTopic.DDD: ['DomainConcept', 'DDDConcept'],
            SoftwareDesignTopic.QUALITY: ['QualityAttribute', 'QualityMetric'],
            SoftwareDesignTopic.CODE_STRUCTURE: ['CodeStructure', 'OrganizationPrinciple']
        }
        return mapping.get(topic, ['DesignPrinciple'])  # Default fallback

    def _get_search_depth(self, question_type: QuestionType) -> int:
        """Determine how deep to search in the graph based on question type"""
        depth_mapping = {
            QuestionType.EXPLANATION: 2,
            QuestionType.COMPARISON: 3,  # Need to find multiple concepts
            QuestionType.APPLICATION: 2,
            QuestionType.ANALYSIS: 3,
            QuestionType.TROUBLESHOOTING: 2
        }
        return depth_mapping.get(question_type, 2)

    def _get_relevant_relationships(self, question_type: QuestionType) -> List[str]:
        """Get relevant relationship types based on question type"""
        relationship_mapping = {
            QuestionType.EXPLANATION: ['CONTAINS', 'RELATES_TO', 'IMPLEMENTS'],
            QuestionType.COMPARISON: ['SIMILAR_TO', 'DIFFERS_FROM', 'RELATES_TO'],
            QuestionType.APPLICATION: ['IMPLEMENTS', 'USES', 'APPLIES_TO'],
            QuestionType.ANALYSIS: ['EVALUATES', 'AFFECTS', 'RELATES_TO'],
            QuestionType.TROUBLESHOOTING: ['VIOLATES', 'CONFLICTS_WITH', 'FIXES']
        }
        return relationship_mapping.get(question_type, ['CONTAINS', 'RELATES_TO'])


# Example usage and testing
if __name__ == "__main__":
    classifier = IntentClassifier()
    
    # Test queries
    test_queries = [
        "What is the Singleton pattern?",
        "Compare Factory and Builder patterns",
        "How to implement Observer pattern in Java?",
        "Is my code violating SOLID principles?",
        "Explain the difference between MVC and MVP",
        "What are the advantages of microservices architecture?"
    ]
    
    for query in test_queries:
        result = classifier.classify_intent(query)
        search_params = classifier.get_search_parameters(result)
        
        print(f"\nQuery: {query}")
        print(f"Question Type: {result['question_type'].value}")
        print(f"Topic: {result['topic'].value}")
        print(f"Confidence: {result['overall_confidence']:.2f}")
        print(f"Keywords: {result['keywords_found']}")
        print(f"Search Parameters: {search_params}")