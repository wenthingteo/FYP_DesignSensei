from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from core.views import auth_views
from core.views.api_views import ConversationViewSet, MessageViewSet
from core.views.chatbot_views import ChatbotAPIView
from core.views.feedback_views import FeedbackView

# Base router for conversations
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')

# Nested router for messages inside conversations
convo_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
convo_router.register(r'messages', MessageViewSet, basename='conversation-messages')


urlpatterns = [
    # Health check
    path('ping/', auth_views.ping, name='api_ping'), # Removed 'api/' prefix

    # === Auth-related API endpoints ===
    path('login/', auth_views.login, name='api_login'), # Removed 'api/' prefix
    path('register/', auth_views.register, name='api_register'), # Removed 'api/' prefix
    path('logout/', auth_views.logout, name='api_logout'), # Removed 'api/' prefix
    path('feedback/', FeedbackView.as_view(), name='api_feedback'), # Removed 'api/' prefix

    # === Chat-related API endpoints ===
    path('chat/', ChatbotAPIView.as_view(), name='chatbot_api'), # Removed 'api/' prefix

    # === DRF viewsets ===
    path('', include(router.urls)),
    path('', include(convo_router.urls)),
]