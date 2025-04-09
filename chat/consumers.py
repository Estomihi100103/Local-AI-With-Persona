# personaai/chat/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import ChatSession, Message
from chat.rag.graph import RAGState, query_preprocessing, retrieve_documents, filter_documents, build_context
from chat.rag.llm import generate_streaming_response_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        self.user = self.scope['user']
        self.response_text = ""

        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        print(f"Received message: {message_content}")
        session_id = text_data_json.get('session_id', self.session_id)

        # Reset response accumulator
        self.response_text = ""

        # Save user message to database
        await self.save_user_message(session_id, message_content)

        # Get chat history for RAG context
        chat_history = await self.get_chat_history(session_id)

        # Start processing response
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'assistant_response_start',
            }
        )

        # Process response using RAG pipeline and streaming
        asyncio.create_task(self.process_streaming_response(message_content, chat_history, session_id))

    async def process_streaming_response(self, query, chat_history, session_id):
        """Process the query with the RAG pipeline and stream the response"""
        print("testing")
        try:
            # Initialize RAG state
            state = RAGState(
                original_query=query,
                refined_query="",
                retrieved_documents=[],
                relevant_context="",
                response="",
                chat_history=chat_history or []
            )
            
            # Run the RAG pipeline steps manually (not using the full graph to enable streaming)
            # 1. Preprocess query
            # state = await database_sync_to_async(query_preprocessing)(state)
            
            # 2. Retrieve documents
            state = await database_sync_to_async(retrieve_documents)(state)
            
            # 3. Filter documents
            # state = await database_sync_to_async(filter_documents)(state)
            
            # 4. Build context
            # state = await database_sync_to_async(build_context)(state)
            
            # 5. Generate streaming response
            async def token_callback(token):
                self.response_text += token
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'assistant_response_chunk',
                        'message': token,
                    }
                )
            
            # Generate the response with streaming
            await generate_streaming_response_async(state, token_callback)
            
            # Save the complete response to database
            await self.save_assistant_message(session_id, self.response_text)
            
            # Send end of response signal
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'assistant_response_end',
                }
            )
            
        except Exception as e:
            # Handle errors
            error_msg = f"An error occurred: {str(e)}"
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'assistant_response_chunk',
                    'message': error_msg,
                }
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'assistant_response_end',
                }
            )
            
            # Save error message to database
            await self.save_assistant_message(session_id, error_msg)

    # Event handler for start of assistant response
    async def assistant_response_start(self, event):
        await self.send(text_data=json.dumps({
            'type': 'assistant_response_start',
        }))

    # Event handler for assistant response chunks
    async def assistant_response_chunk(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'assistant_response_chunk',
            'message': message,
        }))

    # Event handler for end of assistant response
    async def assistant_response_end(self, event):
        await self.send(text_data=json.dumps({
            'type': 'assistant_response_end',
        }))

    @database_sync_to_async
    def save_user_message(self, session_id, content):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        Message.objects.create(
            session=session,
            role=Message.Role.USER,
            content=content
        )

    @database_sync_to_async
    def save_assistant_message(self, session_id, content):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        Message.objects.create(
            session=session,
            role=Message.Role.ASSISTANT,
            content=content
        )

    @database_sync_to_async
    def get_chat_history(self, session_id):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        messages = Message.objects.filter(session=session).order_by('timestamp')
        return [{"role": msg.role, "content": msg.content} for msg in messages]