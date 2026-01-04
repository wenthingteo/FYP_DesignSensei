"""
Unit tests for Chatbot Views
Tests the main chatbot API endpoints and message processing logic
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from core.models import Conversation, Message
from core.views.chatbot_views import ChatbotAPIView


class ChatbotAPIViewTests(TestCase):
    """Test cases for ChatbotAPIView"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
    def tearDown(self):
        """Clean up after tests"""
        User.objects.all().delete()
        Conversation.objects.all().delete()
        Message.objects.all().delete()
    
    def test_authentication_required(self):
        """Test that authentication is required"""
        client = APIClient()  # Unauthenticated client
        response = client.post('/api/chat/', {
            'content': 'What is singleton pattern?',
        })
        # Django returns 403 Forbidden for unauthenticated requests with CSRF protection
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_missing_content(self):
        """Test handling of missing message content"""
        response = self.client.post('/api/chat/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_create_new_conversation_with_first_message(self):
        """Test creating a new conversation with first message"""
        with patch('core.views.chatbot_views.ChatbotAPIView._process_message_async') as mock_process:
            mock_process.return_value = (
                {'response': 'Test response', 'metadata': {'mode': 'LLM_ONLY', 'score': 0.0, 'intent': {}}},
                {'results': []}
            )
            
            response = self.client.post('/api/chat/', {
                'content': 'What is singleton pattern?',
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('conversation_id', response.data)
            self.assertIn('ai_response', response.data)
            
            # Verify conversation was created
            self.assertEqual(Conversation.objects.count(), 1)
            conversation = Conversation.objects.first()
            self.assertEqual(conversation.user, self.user)
            
            # Verify messages were saved
            self.assertEqual(Message.objects.count(), 2)  # User + Bot
    
    def test_add_message_to_existing_conversation(self):
        """Test adding message to existing conversation"""
        conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        with patch('core.views.chatbot_views.ChatbotAPIView._process_message_async') as mock_process:
            mock_process.return_value = (
                {'response': 'Test response', 'metadata': {'mode': 'LLM_ONLY', 'score': 0.0, 'intent': {}}},
                {'results': []}
            )
            
            response = self.client.post('/api/chat/', {
                'content': 'Tell me more about it',
                'conversation': conversation.id,
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(Message.objects.count(), 2)
    
    @patch('core.views.chatbot_views.ChatbotAPIView._process_message_async')
    def test_out_of_scope_detection(self, mock_process):
        """Test out-of-scope question detection"""
        mock_process.return_value = (
            {
                'response': "I'm sorry, but I'm specialized in software design topics only.",
                'metadata': {'mode': 'OUT_OF_SCOPE', 'score': 0.0, 'intent': {'question_type': 'out_of_scope_general'}}
            },
            {'results': []}
        )
        
        response = self.client.post('/api/chat/', {
            'content': 'What should I eat for lunch?',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('specialized in software design', response.data['ai_response']['content'])
    
    def test_regenerate_response(self):
        """Test regenerating last response"""
        conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        # Create initial messages
        Message.objects.create(
            conversation=conversation,
            sender='user',
            content='What is factory pattern?'
        )
        bot_message = Message.objects.create(
            conversation=conversation,
            sender='bot',
            content='Old response'
        )
        
        with patch('core.views.chatbot_views.ChatbotAPIView._process_message_async') as mock_process:
            mock_process.return_value = (
                {'response': 'New regenerated response', 'metadata': {'mode': 'LLM_ONLY', 'score': 0.0, 'intent': {}}},
                {'results': []}
            )
            
            response = self.client.post('/api/chat/', {
                'content': 'What is factory pattern?',
                'conversation': conversation.id,
                'is_regenerate': True,
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify new message was created
            bot_messages = Message.objects.filter(sender='bot')
            self.assertEqual(bot_messages.count(), 2)  # Old and new
            new_bot_message = bot_messages.last()
            self.assertEqual(new_bot_message.content, 'New regenerated response')
    
    def test_conversation_title_generation(self):
        """Test automatic conversation title generation"""
        with patch('core.views.chatbot_views.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='Singleton Pattern Discussion'))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            view = ChatbotAPIView()
            title = view._generate_conversation_title('What is the singleton design pattern?')
            
            self.assertIsInstance(title, str)
            self.assertLessEqual(len(title), 60)
    
    def test_fallback_title_generation(self):
        """Test fallback title generation when API fails"""
        view = ChatbotAPIView()
        title = view._fallback_title('This is a very long message that should be truncated to fit within the maximum character limit for conversation titles')
        
        self.assertIsInstance(title, str)
        self.assertLessEqual(len(title), 61)  # 60 chars + ellipsis


class IntentClassificationTests(TestCase):
    """Test cases for intent classification"""
    
    def setUp(self):
        """Set up intent classifier"""
        from prompt_engine.intent_classifier import IntentClassifier
        self.classifier = IntentClassifier()
    
    def test_explanation_intent(self):
        """Test explanation question detection"""
        result = self.classifier.classify_intent("What is the singleton pattern?")
        self.assertEqual(result['question_type'], 'explanation')
    
    def test_comparison_intent(self):
        """Test comparison question detection"""
        result = self.classifier.classify_intent("What is the difference between factory and abstract factory?")
        self.assertEqual(result['question_type'], 'comparison')
    
    def test_application_intent(self):
        """Test application question detection"""
        result = self.classifier.classify_intent("How to implement observer pattern in Python?")
        self.assertEqual(result['question_type'], 'application')
    
    def test_out_of_scope_detection(self):
        """Test out-of-scope question detection"""
        queries = [
            "What should I eat for lunch?",
            "Tell me a joke",
            "What's the weather today?",
            "Best restaurants in Malaysia",
        ]
        
        for query in queries:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['question_type'], 'out_of_scope_general',
                           f"Failed to detect out-of-scope: {query}")
    
    def test_topic_classification(self):
        """Test topic detection"""
        test_cases = [
            ("singleton pattern", "design_patterns"),
            ("SOLID principles", "solid_principles"),
            ("microservices architecture", "architecture"),
        ]
        
        for query, expected_topic in test_cases:
            result = self.classifier.classify_intent(query)
            self.assertEqual(result['topic'], expected_topic,
                           f"Failed topic classification for: {query}")


class MessageProcessingTests(TestCase):
    """Test cases for async message processing"""
    
    def setUp(self):
        """Set up test environment"""
        self.view = ChatbotAPIView()
    
    @patch('core.views.chatbot_views.client')
    def test_llm_only_mode(self, mock_client):
        """Test LLM_ONLY mode processing"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='Test LLM response'))]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock Neo4j as unavailable
        self.view.graph_search_service = None
        
        import asyncio
        result = asyncio.run(self.view._process_message_async(
            'What is singleton?',
            'test_session',
            {}
        ))
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn('response', result[0])
        self.assertEqual(result[0]['metadata']['mode'], 'LLM_ONLY')
