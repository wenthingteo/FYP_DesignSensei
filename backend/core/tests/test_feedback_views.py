"""
Unit tests for Feedback Views
Tests feedback submission and admin dashboard functionality
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Feedback


class FeedbackViewTests(TestCase):
    """Test cases for feedback submission"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_submit_feedback_authenticated(self):
        """Test submitting feedback as authenticated user"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/feedback/', {
            'comment': 'Great chatbot!',
            'rating': 5,
            'feedbackType': 'general',
            'name': 'Test User',
            'email': 'test@example.com',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(Feedback.objects.count(), 1)
        
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.feedback_type, 'general')
    
    def test_submit_feedback_anonymous(self):
        """Test submitting feedback without authentication"""
        response = self.client.post('/api/feedback/', {
            'comment': 'Anonymous feedback',
            'rating': 4,
            'feedbackType': 'bug',
            'name': 'Anonymous',
            'email': 'anon@example.com',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Feedback.objects.count(), 1)
        
        feedback = Feedback.objects.first()
        self.assertIsNone(feedback.user)
        self.assertEqual(feedback.name, 'Anonymous')
    
    def test_submit_feedback_missing_comment(self):
        """Test submitting feedback without comment"""
        response = self.client.post('/api/feedback/', {
            'rating': 3,
            'feedbackType': 'feature',
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_feedback_type_choices(self):
        """Test different feedback type options"""
        self.client.force_authenticate(user=self.user)
        
        feedback_types = ['bug', 'feature', 'general']
        
        for fb_type in feedback_types:
            response = self.client.post('/api/feedback/', {
                'comment': f'Testing {fb_type}',
                'rating': 3,
                'feedbackType': fb_type,
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(Feedback.objects.count(), 3)


class AdminFeedbackViewTests(TestCase):
    """Test cases for admin feedback dashboard"""
    
    def setUp(self):
        """Set up test users and feedback"""
        self.client = APIClient()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test feedback
        Feedback.objects.create(
            user=self.regular_user,
            comment='Test feedback 1',
            rating=5,
            feedback_type='general'
        )
        Feedback.objects.create(
            comment='Anonymous feedback',
            rating=3,
            feedback_type='bug',
            name='Anonymous User'
        )
    
    def test_admin_can_view_feedback(self):
        """Test that admin can view all feedback"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/admin/feedback/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['feedbacks']), 2)
    
    def test_regular_user_cannot_view_feedback(self):
        """Test that regular user cannot access admin feedback"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/api/admin/feedback/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
    
    def test_unauthenticated_cannot_view_feedback(self):
        """Test that unauthenticated user cannot access feedback"""
        response = self.client.get('/api/admin/feedback/')
        
        # Django returns 403 Forbidden for unauthenticated requests with permission checks
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_delete_feedback(self):
        """Test that admin can delete feedback"""
        self.client.force_authenticate(user=self.admin_user)
        
        feedback = Feedback.objects.first()
        response = self.client.delete(f'/api/admin/feedback/{feedback.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(Feedback.objects.count(), 1)
    
    def test_regular_user_cannot_delete_feedback(self):
        """Test that regular user cannot delete feedback"""
        self.client.force_authenticate(user=self.regular_user)
        
        feedback = Feedback.objects.first()
        response = self.client.delete(f'/api/admin/feedback/{feedback.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_nonexistent_feedback(self):
        """Test deleting feedback that doesn't exist"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete('/api/admin/feedback/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_feedback_display_format(self):
        """Test feedback data format in response"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/admin/feedback/')
        
        feedback = response.data['feedbacks'][0]
        self.assertIn('id', feedback)
        self.assertIn('user', feedback)
        self.assertIn('email', feedback)
        self.assertIn('comment', feedback)
        self.assertIn('rating', feedback)
        self.assertIn('feedback_type', feedback)
        self.assertIn('created_at', feedback)
