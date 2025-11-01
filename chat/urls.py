from django.urls import path
from .views import (
    ChatInterfaceView,
    AgentDashboardView,
    AgentChatView,
    FAQListView,
    GetChatHistoryView
)

app_name = 'chat'

urlpatterns = [
    path('', ChatInterfaceView.as_view(), name='chat_interface'),
    path('faq/', FAQListView.as_view(), name='faq_list'),
    path('agent/dashboard/', AgentDashboardView.as_view(), name='agent_dashboard'),
    path('agent/chat/<str:session_id>/', AgentChatView.as_view(), name='agent_chat'),
    path('api/history/<str:session_id>/', GetChatHistoryView.as_view(), name='chat_history'),
]
