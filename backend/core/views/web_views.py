from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse

from core.models import Conversation, Message, Feedback
from core.services.openai_services import ask_openai

@login_required(login_url='login')
def chatbot(request):
    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
    conversation_id = request.GET.get('cid')
    
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            conversation = None
    else:
        conversation = conversations.first() if conversations.exists() else None

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if not message_text:
            return JsonResponse({'error': 'Message is required'}, status=400)

        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                created_at=timezone.now()
            )

        if not conversation.title or conversation.title.strip() == '':
            conversation.title = message_text[:50]
            conversation.save()

        user_message = Message.objects.create(
            conversation=conversation,
            sender=request.user.username,
            content=message_text,
            created_at=timezone.now(),
        )

        # ai_response_text = ask_openai(message_text)  
        ai_response_text = 'This is AI response'

        Message.objects.create(
            conversation=conversation,
            sender='AI Chatbot',
            content=ai_response_text,
            created_at=timezone.now(),
        )

        return JsonResponse({'message': message_text, 'response': ai_response_text})

    messages = Message.objects.filter(conversation=conversation).order_by('created_at') if conversation else []

    context = {
        'conversations': conversations,
        'current_conversation': conversation,
        'messages': messages,
    }
    return render(request, 'chatbot.html', context)

@require_POST
@login_required
def new_conversation(request):
    conversation = Conversation.objects.create(
        user=request.user,
        title='New Conversation',
        created_at=timezone.now()
    )
    return redirect(f"{reverse('chatbot')}?cid={conversation.id}")


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Passwords do not match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')


def logout(request):
    auth.logout(request)
    return redirect('login')


@login_required(login_url='login')
def feedback(request):
    if request.method == 'POST':
        comment = request.POST.get('comment')
        if comment:
            Feedback.objects.create(user=request.user, comment=comment)
            return render(request, 'feedback.html', {'success': True})
    return render(request, 'feedback.html')
