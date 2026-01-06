from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from core.views import jwt_auth_views
from core.views.api_views import ConversationViewSet, MessageViewSet
from core.views.chatbot_views import ChatbotAPIView
from core.views.feedback_views import FeedbackView, AdminFeedbackView
from core.views.password_reset_views import (
    PasswordResetRequestView,
    PasswordResetValidateView,
    PasswordResetConfirmView
)
from core.views.evaluation_views import (
    PerformanceReportView,
    EvaluationDashboardView,
    GroundTruthManagementView
)

# Base router for conversations
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')

# Nested router for messages inside conversations
convo_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
convo_router.register(r'messages', MessageViewSet, basename='conversation-messages')


urlpatterns = [
    # Health check
    path('ping/', jwt_auth_views.ping, name='api_ping'),

    # JWT Auth endpoints
    path('register/', jwt_auth_views.register, name='api_register'),
    path('login/', jwt_auth_views.login, name='api_login'),
    path('logout/', jwt_auth_views.logout, name='api_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password reset endpoints
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/validate/', PasswordResetValidateView.as_view(), name='password_reset_validate'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    path('feedback/', FeedbackView.as_view(), name='api_feedback'),
    path('admin/feedback/', AdminFeedbackView.as_view(), name='admin_feedback_list'),
    path('admin/feedback/<int:feedback_id>/', AdminFeedbackView.as_view(), name='admin_feedback_delete'),

    # Chat-related API endpoints
    path('chat/', ChatbotAPIView.as_view(), name='chatbot_api'),

    # Evaluation & FYP Objective Endpoints
    path('evaluation/performance-report/', PerformanceReportView.as_view(), name='performance_report'),
    path('evaluation/dashboard/', EvaluationDashboardView.as_view(), name='evaluation_dashboard'),
    path('evaluation/ground-truth/', GroundTruthManagementView.as_view(), name='ground_truth_management'),

    # DRF viewsets
    path('', include(router.urls)),
    path('', include(convo_router.urls)),
]