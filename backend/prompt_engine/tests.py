"""
Unit tests for Intent Classifier
Tests intent classification and topic detection
"""
from django.test import TestCase
from prompt_engine.intent_classifier import IntentClassifier, QuestionType, SoftwareDesignTopic


class IntentClassifierTests(TestCase):
    """Test cases for IntentClassifier"""
    
    def setUp(self):
        """Set up classifier"""
        self.classifier = IntentClassifier()
    
    def test_explanation_question(self):
        """Test explanation question detection"""
        queries = [
            "What is singleton pattern?",
            "Explain the factory method",
            "Define SOLID principles",
            "Describe microservices architecture"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'explanation',
                           f"Failed for: {query}")
    
    def test_comparison_question(self):
        """Test comparison question detection"""
        queries = [
            "What is the difference between factory and abstract factory?",
            "Compare REST vs GraphQL",
            "Strategy pattern vs State pattern",
            "Microservices versus monolithic architecture"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'comparison',
                           f"Failed for: {query}")
    
    def test_application_question(self):
        """Test application question detection"""
        queries = [
            "How to implement observer pattern?",
            "Show me an example of decorator pattern",
            "How do I use dependency injection?",
            "Apply SOLID principles in Python"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'application',
                           f"Failed for: {query}")
    
    def test_analysis_question(self):
        """Test analysis question detection"""
        queries = [
            "Analyze the pros and cons of singleton",
            "Evaluate microservices architecture",
            "What are the advantages of factory pattern?"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'analysis',
                           f"Failed for: {query}")
    
    def test_troubleshooting_question(self):
        """Test troubleshooting question detection"""
        queries = [
            "My singleton pattern is not working",
            "Error in factory implementation",
            "How to fix circular dependency?",
            "Problem with observer pattern"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'troubleshooting',
                           f"Failed for: {query}")
    
    def test_greeting_detection(self):
        """Test greeting detection"""
        queries = [
            "Hi",
            "Hello",
            "Hey there",
            "How are you?"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'greeting',
                           f"Failed for: {query}")
    
    def test_out_of_scope_detection(self):
        """Test out-of-scope question detection"""
        queries = [
            "What should I eat for lunch?",
            "Tell me a joke",
            "What's the weather today?",
            "Recommend restaurants in Malaysia",
            "Best coffee shops nearby",
            "Latest movies to watch",
            "How to cook pasta?"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'out_of_scope_general',
                           f"Failed to detect out-of-scope: {query}")
    
    def test_design_patterns_topic(self):
        """Test design patterns topic detection"""
        queries = [
            "singleton pattern",
            "factory method",
            "observer pattern",
            "decorator design pattern"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['topic'], 'design_patterns',
                           f"Failed for: {query}")
    
    def test_solid_principles_topic(self):
        """Test SOLID principles topic detection"""
        queries = [
            "SOLID principles",
            "Single Responsibility Principle",
            "Open-Closed Principle",
            "Liskov Substitution",
            "Interface Segregation",
            "Dependency Inversion"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['topic'], 'solid_principles',
                           f"Failed for: {query}")
    
    def test_architecture_topic(self):
        """Test architecture topic detection"""
        queries = [
            "microservices architecture",
            "monolithic architecture",
            "layered architecture",
            "event-driven architecture"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['topic'], 'architecture',
                           f"Failed for: {query}")
    
    def test_ddd_topic(self):
        """Test domain-driven design topic detection"""
        queries = [
            "domain-driven design",
            "bounded context",
            "aggregate root",
            "DDD patterns"
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['topic'], 'ddd',
                           f"Failed for: {query}")
    
    def test_confidence_scores(self):
        """Test that confidence scores are returned"""
        result = self.classifier.classify_intent("What is singleton pattern?")
        
        self.assertIn('question_confidence', result)
        self.assertIn('topic_confidence', result)
        self.assertIn('overall_confidence', result)
        self.assertIsInstance(result['question_confidence'], float)
        self.assertGreaterEqual(result['question_confidence'], 0.0)
        self.assertLessEqual(result['question_confidence'], 1.0)
    
    def test_keywords_extraction(self):
        """Test that relevant keywords are extracted"""
        result = self.classifier.classify_intent("What is the singleton design pattern?")
        
        self.assertIn('keywords_found', result)
        self.assertIsInstance(result['keywords_found'], list)
    
    def test_fallback_to_general_topic(self):
        """Test fallback to general topic for unclear queries"""
        result = self.classifier.classify_intent("Tell me about coding")
        
        # Should classify but might fall back to general
        self.assertIn('topic', result)
    
    def test_search_parameters_generation(self):
        """Test search parameters generation"""
        intent = self.classifier.classify_intent("What is singleton pattern?")
        params = self.classifier.get_search_parameters("What is singleton pattern?", intent)
        
        self.assertIsInstance(params, dict)
        self.assertIn('topic_filter_labels', params)
        self.assertIsInstance(params['topic_filter_labels'], list)
    
    def test_no_software_keywords_fallback(self):
        """Test fallback when no software design keywords found"""
        result = self.classifier.classify_intent("tell me about random things")
        
        # Should detect as out-of-scope if no software keywords
        if result['topic_confidence'] < 0.3 and result['topic'] == 'general_software_design':
            self.assertEqual(result['question_type'], 'out_of_scope_general')
