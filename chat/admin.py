from django.contrib import admin
from .models import FAQ, ChatSession, ChatMessage


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('question', 'answer', 'keywords')
    ordering = ('-created_at',)
    list_per_page = 25


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'customer', 'agent', 'status', 'started_at', 'ended_at')
    list_filter = ('status', 'started_at')
    search_fields = ('session_id', 'customer__username', 'agent__username', 'customer_name')
    ordering = ('-started_at',)
    readonly_fields = ('session_id', 'started_at', 'agent_joined_at', 'ended_at')
    list_per_page = 25


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender_type', 'sender', 'message_preview', 'timestamp', 'is_read')
    list_filter = ('sender_type', 'timestamp', 'is_read')
    search_fields = ('message', 'session__session_id', 'sender__username')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    list_per_page = 50

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
