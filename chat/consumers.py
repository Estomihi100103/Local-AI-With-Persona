# personaai/chat/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import ChatSession, Message
from chat.rag.retriever import DocumentRetriever
from chat.rag.llm import generate_streaming_response, create_conversation_prompt, build_context
from langchain.memory import ConversationBufferMemory

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        self.user = self.scope['user']
        self.response_text = ""
        self.memory = ConversationBufferMemory(return_messages=True)  # Memori per sesi

        if not self.user.is_authenticated:
            await self.close()
            return

        # Muat riwayat awal dari database saat koneksi dibuka
        self.memory = await self.get_or_create_memory(self.session_id)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        session_id = text_data_json.get('session_id', self.session_id)

        self.response_text = ""
        await self.save_user_message(session_id, message_content)

        await self.channel_layer.group_send(self.room_group_name, {'type': 'assistant_response_start'})
        asyncio.create_task(self.process_streaming_response(message_content, session_id))

    async def process_streaming_response(self, query, session_id):
        try:
            # Retrieve dokumen
            retriever = DocumentRetriever()
            retrieved_docs = retriever.invoke(query)
            context = build_context(retrieved_docs)
            
            # Callback untuk streaming
            async def token_callback(token):
                self.response_text += token
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'assistant_response_chunk', 'message': token}
                )

            # Generate respons dengan streaming
            full_response = await generate_streaming_response(query, context, self.memory, token_callback)

            await self.save_assistant_message(session_id, full_response)
            await self.channel_layer.group_send(self.room_group_name, {'type': 'assistant_response_end'})

        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            await self.channel_layer.group_send(self.room_group_name, {'type': 'assistant_response_chunk', 'message': error_msg})
            await self.channel_layer.group_send(self.room_group_name, {'type': 'assistant_response_end'})
            await self.save_assistant_message(session_id, error_msg)

    async def assistant_response_start(self, event):
        await self.send(text_data=json.dumps({'type': 'assistant_response_start'}))

    async def assistant_response_chunk(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'type': 'assistant_response_chunk', 'message': message}))

    async def assistant_response_end(self, event):
        await self.send(text_data=json.dumps({'type': 'assistant_response_end'}))

    @database_sync_to_async
    def save_user_message(self, session_id, content):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        Message.objects.create(session=session, role=Message.Role.USER, content=content)

    @database_sync_to_async
    def save_assistant_message(self, session_id, content):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        Message.objects.create(session=session, role=Message.Role.ASSISTANT, content=content)

    @database_sync_to_async
    def get_chat_history(self, session_id):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        messages = Message.objects.filter(session=session).order_by('timestamp')
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def load_initial_history(self):
        chat_history = await self.get_chat_history(self.session_id)
        for msg in chat_history:
            if msg["role"] == "user":
                self.memory.save_context({"input": msg["content"]}, {"output": ""})
            elif msg["role"] == "assistant":
                self.memory.save_context({"input": ""}, {"output": msg["content"]})
                

    @database_sync_to_async
    def get_or_create_memory(self, session_id):
        """Get or create memory for this session"""
        # Cek apakah memory sudah ada dalam cache (opsional, dapat menggunakan Django cache)
        memory = ConversationBufferMemory(return_messages=True)
        
        # Muat history dari database
        session = ChatSession.objects.get(id=session_id, user=self.user)
        messages = Message.objects.filter(session=session).order_by('timestamp')
        
        # Rekonstruksi memory
        last_user_input = None
        for msg in messages:
            if msg.role == Message.Role.USER:
                last_user_input = msg.content
            elif msg.role == Message.Role.ASSISTANT and last_user_input:
                memory.save_context({"input": last_user_input}, {"output": msg.content})
                last_user_input = None
        
        return memory