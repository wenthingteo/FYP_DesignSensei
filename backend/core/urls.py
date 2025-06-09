from django.urls import path, include
from core.views import web_views as views
from core.views.api_views import ConversationViewSet, MessageViewSet
from core.views.web_views import new_conversation
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversations')

convo_router = NestedDefaultRouter(router, r'conversations', lookup='conversation')
convo_router.register(r'messages', MessageViewSet, basename='conversation-messages')

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('new_conversation/', new_conversation, name='new_conversation'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('feedback/', views.feedback, name='feedback'),
    path('api/', include(router.urls)),
    path('api/', include(convo_router.urls)),
]
