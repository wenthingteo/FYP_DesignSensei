"""
Unit tests for Models
Tests database models and their methods
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Conversation, Message, Feedback, EvaluationRecord, GroundTruth, PasswordResetToken
from datetime import timedelta


class ConversationModelTests(TestCase):
    """Test cases for Conversation model"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_conversation(self):
        """Test creating a conversation"""
        conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.title, 'Test Conversation')
        self.assertIsNotNone(conversation.created_at)
        self.assertIsNotNone(conversation.updated_at)
    
    def test_conversation_default_title(self):
        """Test default conversation title"""
        conversation = Conversation.objects.create(user=self.user)
        
        self.assertEqual(conversation.title, 'New Conversation')
    
    def test_conversation_string_representation(self):
        """Test conversation __str__ method"""
        conversation = Conversation.objects.create(
            user=self.user,
            title='Design Patterns'
        )
        
        expected = f'Design Patterns by testuser'
        self.assertEqual(str(conversation), expected)
    
    def test_conversation_updated_at_changes(self):
        """Test that updated_at changes when conversation is modified"""
        conversation = Conversation.objects.create(
            user=self.user,
            title='Original Title'
        )
        original_updated_at = conversation.updated_at
        
        # Wait a moment and update
        conversation.title = 'Updated Title'
        conversation.save()
        
        self.assertGreater(conversation.updated_at, original_updated_at)


class MessageModelTests(TestCase):
    """Test cases for Message model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
    
    def test_create_user_message(self):
        """Test creating a user message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender='user',
            content='What is singleton pattern?'
        )
        
        self.assertEqual(message.sender, 'user')
        self.assertEqual(message.content, 'What is singleton pattern?')
        self.assertIsNotNone(message.created_at)
    
    def test_create_bot_message(self):
        """Test creating a bot message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender='bot',
            content='The singleton pattern ensures...'
        )
        
        self.assertEqual(message.sender, 'bot')
    
    def test_message_with_metadata(self):
        """Test message with metadata"""
        metadata = {
            'mode': 'GRAPH_RAG',
            'score': 0.87,
            'intent': {'question_type': 'explanation'}
        }
        
        message = Message.objects.create(
            conversation=self.conversation,
            sender='bot',
            content='Response with metadata',
            metadata=metadata
        )
        
        self.assertEqual(message.metadata['mode'], 'GRAPH_RAG')
        self.assertEqual(message.metadata['score'], 0.87)
    
    def test_message_string_representation(self):
        """Test message __str__ method"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender='user',
            content='This is a test message with more than 30 characters'
        )
        
        str_repr = str(message)
        self.assertIn('User', str_repr)
        self.assertTrue(len(str_repr) < 100)


class FeedbackModelTests(TestCase):
    """Test cases for Feedback model"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_feedback_with_user(self):
        """Test creating feedback with authenticated user"""
        feedback = Feedback.objects.create(
            user=self.user,
            comment='Great chatbot!',
            rating=5,
            feedback_type='general'
        )
        
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.feedback_type, 'general')
    
    def test_create_anonymous_feedback(self):
        """Test creating anonymous feedback"""
        feedback = Feedback.objects.create(
            name='Anonymous User',
            email='anon@example.com',
            comment='Anonymous feedback',
            rating=4,
            feedback_type='bug'
        )
        
        self.assertIsNone(feedback.user)
        self.assertEqual(feedback.name, 'Anonymous User')
        self.assertEqual(feedback.feedback_type, 'bug')
    
    def test_feedback_type_choices(self):
        """Test feedback type choices"""
        feedback_types = ['bug', 'feature', 'general']
        
        for fb_type in feedback_types:
            feedback = Feedback.objects.create(
                user=self.user,
                comment=f'Test {fb_type}',
                rating=3,
                feedback_type=fb_type
            )
            self.assertEqual(feedback.feedback_type, fb_type)
    
    def test_feedback_default_rating(self):
        """Test default rating is 0"""
        feedback = Feedback.objects.create(
            user=self.user,
            comment='No rating provided',
            feedback_type='general'
        )
        
        self.assertEqual(feedback.rating, 0)
    
    def test_feedback_string_representation(self):
        """Test feedback __str__ method"""
        feedback = Feedback.objects.create(
            user=self.user,
            comment='Test feedback',
            rating=5,
            feedback_type='general'
        )
        
        str_repr = str(feedback)
        self.assertIn('testuser', str_repr)


class EvaluationRecordModelTests(TestCase):
    """Test cases for EvaluationRecord model"""
    
    def setUp(self):
        """Set up test data"""
        self.ground_truth = GroundTruth.objects.create(
            question='What is singleton pattern?',
            ground_truth='The singleton pattern ensures a class has only one instance...',
            verified=True
        )
    
    def test_create_evaluation_record(self):
        """Test creating an evaluation record"""
        record = EvaluationRecord.objects.create(
            session_id='test_session_123',
            user_query='What is singleton?',
            ai_response='The singleton pattern...',
            rag_used=True,
            hybrid_mode='GRAPH_RAG',
            confidence_score=0.87
        )
        
        self.assertEqual(record.session_id, 'test_session_123')
        self.assertTrue(record.rag_used)
        self.assertEqual(record.hybrid_mode, 'GRAPH_RAG')
    
    def test_evaluation_with_ground_truth(self):
        """Test evaluation record linked to ground truth"""
        record = EvaluationRecord.objects.create(
            session_id='test_session',
            user_query='What is singleton pattern?',
            ai_response='Response text',
            matched_ground_truth=self.ground_truth,
            similarity_to_truth=0.92
        )
        
        self.assertEqual(record.matched_ground_truth, self.ground_truth)
        self.assertEqual(record.similarity_to_truth, 0.92)
    
    def test_evaluation_flagging(self):
        """Test flagging incorrect responses"""
        record = EvaluationRecord.objects.create(
            session_id='test_session',
            user_query='Test query',
            ai_response='Incorrect response',
            flagged_incorrect=True,
            flag_reason='Response contradicts ground truth'
        )
        
        self.assertTrue(record.flagged_incorrect)
        self.assertIsNotNone(record.flag_reason)


class GroundTruthModelTests(TestCase):
    """Test cases for GroundTruth model"""
    
    def test_create_ground_truth(self):
        """Test creating ground truth"""
        gt = GroundTruth.objects.create(
            question='What is factory pattern?',
            context='Design patterns context',
            ground_truth='The factory pattern provides an interface...',
            created_by='admin',
            verified=True
        )
        
        self.assertEqual(gt.question, 'What is factory pattern?')
        self.assertTrue(gt.verified)
    
    def test_ground_truth_string_representation(self):
        """Test ground truth __str__ method"""
        gt = GroundTruth.objects.create(
            question='What is the observer pattern used for?',
            ground_truth='The observer pattern...'
        )
        
        str_repr = str(gt)
        self.assertIn('What is the observer pattern', str_repr)


class PasswordResetTokenModelTests(TestCase):
    """Test cases for PasswordResetToken model"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_token_auto_expiry_setting(self):
        """Test that token sets expiry automatically"""
        token = PasswordResetToken.objects.create(user=self.user)
        
        self.assertIsNotNone(token.expires_at)
        self.assertGreater(token.expires_at, timezone.now())
    
    def test_token_is_valid(self):
        """Test valid token"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertTrue(token.is_valid())
    
    def test_expired_token_is_invalid(self):
        """Test expired token is invalid"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        self.assertFalse(token.is_valid())
    
    def test_used_token_is_invalid(self):
        """Test used token is invalid"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=True
        )
        
        self.assertFalse(token.is_valid())
    
    def test_token_string_representation(self):
        """Test token __str__ method"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        str_repr = str(token)
        self.assertIn('testuser', str_repr)
        self.assertIn('Valid', str_repr)
