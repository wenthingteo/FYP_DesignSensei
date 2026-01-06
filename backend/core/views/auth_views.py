from django.contrib import auth
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
import json

@login_required
def ping(request):
    return JsonResponse({'message': 'User is authenticated', 'username': request.user.username})

@csrf_exempt
@ensure_csrf_cookie
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            response = JsonResponse({'message': 'Login successful', 'username': user.username})
            # Ensure CSRF cookie is set in response
            get_token(request)
            return response
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)

    return JsonResponse({'error': 'POST method required'}, status=405)

@csrf_exempt
@ensure_csrf_cookie
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password1 = data.get('password1')
            password2 = data.get('password2')
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        if password1 != password2:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already taken'}, status=409)

        user = User.objects.create_user(username=username, email=email, password=password1)
        auth.login(request, user)
        response = JsonResponse({'message': 'Registration successful', 'username': user.username})
        # Ensure CSRF cookie is set in response
        get_token(request)
        return response

    return JsonResponse({'error': 'POST method required'}, status=405)

@csrf_exempt
def logout(request):
    if request.user.is_authenticated:
        auth.logout(request)
        return JsonResponse({'message': 'Logout successful'})
    return JsonResponse({'error': 'User not logged in'}, status=400)

# New endpoint to get CSRF token
@ensure_csrf_cookie
def get_csrf_token(request):
    """Endpoint to get CSRF token for authenticated users"""
    return JsonResponse({
        'csrfToken': get_token(request),
        'detail': 'CSRF cookie set'
    })
