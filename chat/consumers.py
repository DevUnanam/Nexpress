import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatSession, ChatMessage, FAQ
from core.models import UserProfile


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat
    Supports both bot and agent conversations
    """

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Get or create chat session
        await self.get_or_create_session()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket
        """
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        message = data.get('message', '')

        if message_type == 'message':
            # Customer message
            await self.handle_customer_message(message)
        elif message_type == 'agent_message':
            # Agent message
            await self.handle_agent_message(message)
        elif message_type == 'request_agent':
            # Customer requests human agent
            await self.handle_agent_request()
        elif message_type == 'agent_join':
            # Agent joins the chat
            await self.handle_agent_join()
        elif message_type == 'close_chat':
            # Close the chat session
            await self.handle_close_chat()

    async def handle_customer_message(self, message):
        """
        Handle customer message - try bot response first
        """
        try:
            session = await self.get_session()

            # Save customer message
            await self.save_message(session, 'customer', message)

            # Send customer message to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': 'customer',
                    'timestamp': timezone.now().isoformat()
                }
            )

            # If not in agent mode, try bot response
            if session.status == 'bot':
                # Add small delay to make it feel more natural
                import asyncio
                await asyncio.sleep(0.5)

                bot_response = await self.get_bot_response(message)
                if bot_response:
                    # Check if user wants to speak to an agent
                    if bot_response == "AGENT_REQUEST":
                        # Automatically escalate to agent
                        await self.handle_agent_request()
                    else:
                        # Save bot message
                        await self.save_message(session, 'bot', bot_response)

                        # Send bot response to room
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'chat_message',
                                'message': bot_response,
                                'sender': 'bot',
                                'timestamp': timezone.now().isoformat()
                            }
                        )
                else:
                    # Bot couldn't answer, suggest agent
                    fallback_message = "I'm sorry, I couldn't find an answer to that. Would you like to speak with a customer care agent?"
                    await self.save_message(session, 'bot', fallback_message)

                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': fallback_message,
                            'sender': 'bot',
                            'timestamp': timezone.now().isoformat(),
                            'show_agent_button': True
                        }
                    )
        except Exception as e:
            print(f"Error in handle_customer_message: {e}")
            import traceback
            traceback.print_exc()

    async def handle_agent_message(self, message):
        """
        Handle agent message
        """
        session = await self.get_session()
        user = self.scope.get('user')

        # Verify user is staff/agent
        if not user or not user.is_authenticated or not user.is_staff:
            return

        # Save agent message
        await self.save_message(session, 'agent', message, user)

        # Send agent message to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': 'agent',
                'sender_name': user.username,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_agent_request(self):
        """
        Customer requests to speak with an agent
        """
        session = await self.get_session()

        # Update session status to waiting
        await self.update_session_status('waiting')

        # Notify customer
        system_message = "Connecting you to an agent. Please wait..."
        await self.save_message(session, 'system', system_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': system_message,
                'sender': 'system',
                'timestamp': timezone.now().isoformat()
            }
        )

        # Notify all agents about new waiting session
        await self.channel_layer.group_send(
            'agents_room',
            {
                'type': 'agent_notification',
                'action': 'new_session',
                'session_id': self.session_id
            }
        )

    async def handle_agent_join(self):
        """
        Agent joins the chat
        """
        user = self.scope.get('user')

        if not user or not user.is_authenticated or not user.is_staff:
            return

        session = await self.get_session()

        # Assign agent to session
        await self.assign_agent(session, user)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Notify customer
        system_message = f"Agent {user.username} has joined the chat. How can I help you?"
        await self.save_message(session, 'system', system_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': system_message,
                'sender': 'system',
                'timestamp': timezone.now().isoformat()
            }
        )

    async def handle_close_chat(self):
        """
        Close the chat session
        """
        session = await self.get_session()
        await self.close_session(session)

        # Notify room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_closed',
                'timestamp': timezone.now().isoformat()
            }
        )

    async def chat_message(self, event):
        """
        Receive message from room group and send to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_name': event.get('sender_name', ''),
            'timestamp': event['timestamp'],
            'show_agent_button': event.get('show_agent_button', False)
        }))

    async def chat_closed(self, event):
        """
        Notify that chat is closed
        """
        await self.send(text_data=json.dumps({
            'type': 'closed',
            'timestamp': event['timestamp']
        }))

    async def agent_notification(self, event):
        """
        Send notification to agents
        """
        await self.send(text_data=json.dumps({
            'type': 'agent_notification',
            'action': event['action'],
            'session_id': event.get('session_id', '')
        }))

    # Database operations (sync to async)

    @database_sync_to_async
    def get_or_create_session(self):
        """
        Get or create chat session
        """
        user = self.scope.get('user')
        session, created = ChatSession.objects.get_or_create(
            session_id=self.session_id,
            defaults={
                'customer': user if user and user.is_authenticated else None,
                'status': 'bot'
            }
        )
        return session

    @database_sync_to_async
    def get_session(self):
        """
        Get chat session
        """
        return ChatSession.objects.get(session_id=self.session_id)

    @database_sync_to_async
    def save_message(self, session, sender_type, message, sender=None):
        """
        Save message to database
        """
        return ChatMessage.objects.create(
            session=session,
            sender_type=sender_type,
            sender=sender,
            message=message
        )

    @database_sync_to_async
    def get_bot_response(self, user_message):
        """
        Get bot response based on user message
        Handles greetings and FAQ menu selection
        """
        user_message_lower = user_message.lower().strip()

        # Check for greeting
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        if any(greeting in user_message_lower for greeting in greetings):
            return self.get_welcome_menu()

        # Check if user selected a number
        if user_message.strip().isdigit():
            return self.get_faq_answer_by_number(int(user_message.strip()))

        # Try keyword matching for direct questions
        faqs = FAQ.objects.filter(is_active=True)

        best_match = None
        best_score = 0

        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'should', 'would', 'what', 'where', 'when', 'why', 'how', 'i', 'my', 'me', 'to', 'for', 'of', 'in', 'on', 'at'}

        for faq in faqs:
            score = 0

            # Check if question contains the user message or vice versa
            if user_message_lower in faq.question.lower():
                score += 5
            if faq.question.lower() in user_message_lower:
                score += 3

            # Check keywords
            keywords = faq.get_keywords_list()
            for keyword in keywords:
                if keyword in user_message_lower:
                    score += 3

            # Check if any significant word in user message is in FAQ question
            user_words = set(word for word in user_message_lower.split() if word not in common_words and len(word) > 2)
            faq_words = set(word for word in faq.question.lower().split() if word not in common_words)

            for keyword in keywords:
                faq_words.update(word for word in keyword.split() if word not in common_words)

            common_significant_words = user_words.intersection(faq_words)
            score += len(common_significant_words) * 2

            if score > best_score:
                best_score = score
                best_match = faq

        # If we found a good match, return the answer
        if best_match and best_score >= 3:
            return best_match.answer

        # If no good match, show the menu
        return self.get_welcome_menu()

    def get_welcome_menu(self):
        """
        Generate welcome message with FAQ menu
        """
        faqs = FAQ.objects.filter(is_active=True).order_by('id')

        if not faqs:
            return "Hello! How may I help you today?"

        menu = "Hello! How may I help you?\n\nPlease select a question by typing the number:\n\n"

        for index, faq in enumerate(faqs, 1):
            menu += f"{index}. {faq.question}\n"

        # Add "Speak to an agent" as the last option
        menu += f"\n{len(faqs) + 1}. Speak to an agent"

        return menu

    def get_faq_answer_by_number(self, number):
        """
        Get FAQ answer by number selection
        """
        faqs = list(FAQ.objects.filter(is_active=True).order_by('id'))

        if not faqs:
            return "I'm sorry, no FAQs are currently available. Would you like to speak to an agent?"

        # Check if user wants to speak to an agent (last option)
        if number == len(faqs) + 1:
            # This will be handled specially by setting a flag
            return "AGENT_REQUEST"

        # Check if number is valid
        if 1 <= number <= len(faqs):
            faq = faqs[number - 1]
            return faq.answer
        else:
            return f"Invalid option. Please select a number between 1 and {len(faqs) + 1}."

    @database_sync_to_async
    def update_session_status(self, status):
        """
        Update session status
        """
        session = ChatSession.objects.get(session_id=self.session_id)
        session.status = status
        session.save()
        return session

    @database_sync_to_async
    def assign_agent(self, session, agent):
        """
        Assign agent to session
        """
        session.assign_agent(agent)
        return session

    @database_sync_to_async
    def close_session(self, session):
        """
        Close the session
        """
        session.close_session()
        return session


class AgentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for agents to monitor and join chats
    """

    async def connect(self):
        self.user = self.scope.get('user')

        # Only allow staff/agents
        if not self.user or not self.user.is_authenticated or not self.user.is_staff:
            await self.close()
            return

        # Join agents room
        await self.channel_layer.group_add(
            'agents_room',
            self.channel_name
        )

        await self.accept()

        # Send list of waiting sessions
        waiting_sessions = await self.get_waiting_sessions()
        await self.send(text_data=json.dumps({
            'type': 'waiting_sessions',
            'sessions': waiting_sessions
        }))

    async def disconnect(self, close_code):
        # Leave agents room
        await self.channel_layer.group_discard(
            'agents_room',
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming messages from agent
        """
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'get_waiting_sessions':
            waiting_sessions = await self.get_waiting_sessions()
            await self.send(text_data=json.dumps({
                'type': 'waiting_sessions',
                'sessions': waiting_sessions
            }))

    async def agent_notification(self, event):
        """
        Receive notification about new waiting sessions
        """
        await self.send(text_data=json.dumps({
            'type': 'agent_notification',
            'action': event['action'],
            'session_id': event.get('session_id', '')
        }))

    @database_sync_to_async
    def get_waiting_sessions(self):
        """
        Get all waiting sessions
        """
        sessions = ChatSession.objects.filter(status='waiting').values(
            'session_id',
            'customer__username',
            'customer_name',
            'started_at'
        )
        return list(sessions)
