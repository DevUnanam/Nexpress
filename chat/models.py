from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class FAQ(models.Model):
    """
    Frequently Asked Questions for the chatbot
    """
    question = models.CharField(
        max_length=500,
        help_text='The question or query'
    )
    answer = models.TextField(
        help_text='The answer to the question'
    )
    keywords = models.TextField(
        help_text='Comma-separated keywords for matching (e.g., track, tracking, shipment)',
        blank=True
    )
    category = models.CharField(
        max_length=100,
        choices=[
            ('shipping', 'Shipping'),
            ('tracking', 'Tracking'),
            ('delivery', 'Delivery'),
            ('refund', 'Refund'),
            ('pickup', 'Pickup'),
            ('pricing', 'Pricing'),
            ('account', 'Account'),
            ('general', 'General'),
        ],
        default='general',
        help_text='Category of the FAQ'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this FAQ is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['-created_at']

    def __str__(self):
        return self.question[:50]

    def get_keywords_list(self):
        """Return keywords as a list"""
        if self.keywords:
            return [kw.strip().lower() for kw in self.keywords.split(',')]
        return []


class ChatSession(models.Model):
    """
    Represents a chat session between a customer and the system (bot or agent)
    """
    SESSION_STATUS = [
        ('bot', 'Bot Only'),
        ('waiting', 'Waiting for Agent'),
        ('active', 'Active with Agent'),
        ('closed', 'Closed'),
    ]

    session_id = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique session identifier'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions',
        help_text='Customer (can be null for anonymous users)'
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name for anonymous customers'
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_sessions',
        help_text='Assigned customer support agent'
    )
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS,
        default='bot',
        help_text='Current status of the chat session'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    agent_joined_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When agent joined the chat'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the chat session ended'
    )

    class Meta:
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.status}"

    def close_session(self):
        """Close the chat session"""
        self.status = 'closed'
        self.ended_at = timezone.now()
        self.save()

    def assign_agent(self, agent):
        """Assign an agent to this session"""
        self.agent = agent
        self.status = 'active'
        self.agent_joined_at = timezone.now()
        self.save()


class ChatMessage(models.Model):
    """
    Individual messages in a chat session
    """
    SENDER_TYPE = [
        ('customer', 'Customer'),
        ('bot', 'Bot'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text='The chat session this message belongs to'
    )
    sender_type = models.CharField(
        max_length=20,
        choices=SENDER_TYPE,
        help_text='Who sent this message'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who sent the message (if applicable)'
    )
    message = models.TextField(
        help_text='The message content'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the message has been read'
    )

    class Meta:
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender_type}: {self.message[:50]}"
