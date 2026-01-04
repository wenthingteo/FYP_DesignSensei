"""
Unit tests for Authentication Views
Tests login, register, logout, and password reset functionality
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from core.models import PasswordResetToken
from datetime import timedelta
from django.utils import timezone


class AuthenticationTests(TestCase):
    """Test cases for authentication endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post('/api/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
        }, format='json')
        
        # Auth view returns 200, not 201
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post('/api/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'pass123',
            'password2': 'different123',
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        User.objects.create_user(**self.user_data)
        
        response = self.client.post('/api/register/', {
            'username': 'testuser',
            'email': 'another@example.com',
            'password1': 'pass123',
            'password2': 'pass123',
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
    
    def test_user_login(self):
        """Test user login"""
        User.objects.create_user(**self.user_data)
        
        response = self.client.post('/api/login/', {
            'username': 'testuser',
            'password': 'testpass123',
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # JsonResponse doesn't have .data, parse json directly
        import json
        data = json.loads(response.content)
        self.assertIn('message', data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        User.objects.create_user(**self.user_data)
        
        response = self.client.post('/api/login/', {
            'username': 'testuser',
            'password': 'wrongpass',
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_logout(self):
        """Test user logout"""
        user = User.objects.create_user(**self.user_data)
        # Use login() to properly authenticate for session-based auth
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post('/api/logout/', format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PasswordResetTests(TestCase):
    """Test cases for password reset functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpass123'
        )
    
    def test_password_reset_token_creation(self):
        """Test creating a password reset token"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertTrue(token.is_valid())
        self.assertIsNotNone(token.token)
    
    def test_password_reset_token_expiry(self):
        """Test that expired tokens are invalid"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        self.assertFalse(token.is_valid())
    
    def test_password_reset_token_used(self):
        """Test that used tokens are invalid"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=1),
            is_used=True
        )
        
        self.assertFalse(token.is_valid())
