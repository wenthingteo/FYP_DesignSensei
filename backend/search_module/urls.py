# --- App Setup: search_app/urls.py ---
# This file defines the URL routing specifically for your 'search_app'.
# Assumes myproject/urls.py includes this app's URLs, e.g., path('api/', include('search_app.urls')).

from django.urls import path
from searchAPIView import SearchAPIView

urlpatterns = [
    path('search/', SearchAPIView.as_view(), name='search-api'),
]