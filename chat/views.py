from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.views import View
import uuid
from .models import ChatSession, ChatMessage, FAQ


class ChatInterfaceView(TemplateView):
    """
    Customer chat interface
    """
    template_name = 'chat/chat_interface.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Generate or get session ID
        session_id = self.request.session.get('chat_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            self.request.session['chat_session_id'] = session_id

        context['session_id'] = session_id

        # Get chat history if session exists
        try:
            session = ChatSession.objects.get(session_id=session_id)
            context['messages'] = session.messages.all()
            context['session'] = session
        except ChatSession.DoesNotExist:
            context['messages'] = []
            context['session'] = None

        return context


class AgentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Agent dashboard for managing chat sessions
    """
    template_name = 'chat/agent_dashboard.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get waiting sessions
        context['waiting_sessions'] = ChatSession.objects.filter(
            status='waiting'
        ).select_related('customer')

        # Get active sessions for this agent
        context['my_active_sessions'] = ChatSession.objects.filter(
            status='active',
            agent=self.request.user
        ).select_related('customer')

        # Get all active sessions
        context['all_active_sessions'] = ChatSession.objects.filter(
            status='active'
        ).select_related('customer', 'agent')

        return context


class AgentChatView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Agent view for a specific chat session
    """
    template_name = 'chat/agent_chat.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = kwargs.get('session_id')

        session = get_object_or_404(ChatSession, session_id=session_id)
        context['session'] = session
        context['messages'] = session.messages.all()

        return context


class FAQListView(ListView):
    """
    Public view to display FAQs
    """
    model = FAQ
    template_name = 'chat/faq_list.html'
    context_object_name = 'faqs'
    paginate_by = 20

    def get_queryset(self):
        queryset = FAQ.objects.filter(is_active=True)

        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                question__icontains=search_query
            ) | queryset.filter(
                answer__icontains=search_query
            ) | queryset.filter(
                keywords__icontains=search_query
            )

        return queryset.order_by('category', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = FAQ._meta.get_field('category').choices
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class GetChatHistoryView(View):
    """
    API endpoint to get chat history for a session
    """
    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(session_id=session_id)
            messages = session.messages.all().values(
                'sender_type',
                'message',
                'timestamp',
                'sender__username'
            )

            return JsonResponse({
                'success': True,
                'messages': list(messages),
                'status': session.status
            })
        except ChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Session not found'
            }, status=404)
