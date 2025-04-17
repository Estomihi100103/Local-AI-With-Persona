from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ChatSession, Message
import uuid
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import ChatSession

# Create your views here.
@login_required
def chat_home(request):
    """Home page showing all chat sessions for a user."""
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'chat/home.html', {'chat_sessions': chat_sessions})

@login_required
def create_session(request):
    """Create a new chat session."""
    if request.method == 'POST':
        title = request.POST.get('title', f"Chat {uuid.uuid4().hex[:8]}")
        session = ChatSession.objects.create(user=request.user, title=title)
        return redirect('chat_detail', session_id=session.id)
    return redirect('chat_home')

@login_required
def chat_detail(request, session_id):
    """Detail view for a specific chat session."""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = Message.objects.filter(session=session).order_by('timestamp')
    
    # Get all chat sessions for sidebar
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    
    return render(request, 'chat/detail.html', {
        'session': session,
        'messages': messages,
        'chat_sessions': chat_sessions
    })
    
