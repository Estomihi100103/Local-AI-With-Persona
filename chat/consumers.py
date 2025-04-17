# personaai/chat/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import ChatSession, Message
from chat.rag.retriever import DocumentRetriever
from chat.rag.generation import generate_streaming_response, create_conversation_prompt, build_context
from langchain.memory import ConversationBufferMemory

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        self.user = self.scope['user']
        self.response_text = ""
        self.memory = ConversationBufferMemory(return_messages=True)

        if not self.user.is_authenticated:
            await self.close()
            return

        self.memory = await self.get_or_create_memory(self.session_id)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Kirim status awal
        session = await self.get_session()
        has_messages = await self.has_messages()
        await self.send(text_data=json.dumps({
            'type': 'session_info',
            'use_persona': session.use_persona,
            'disable_toggle': has_messages,
            'disable_model_select': has_messages,
            'session_id': self.session_id,
            'selected_model': session.selected_model,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        session_id = text_data_json.get('session_id', self.session_id)
        use_persona = text_data_json.get('use_persona', None)
        model = text_data_json.get('model', None)
        message_type = text_data_json.get('type', None)
        
        if message_type == 'select_model' and model:
            # periksa apakah sudah ada pesan dalam sesi
            has_messages = await self.has_messages()
            if has_messages:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Cannot change model after messages exist'
                }))
                return
            
            valid_models = ['gemma3:1b', 'qwen2.5-coder:0.5b', 'deepseek-r1:1.5b']
            if model not in valid_models:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Invalid model: {model}'
                }))
                return
            await self.update_session_model(model)
            await self.send(text_data=json.dumps({
                'type': 'model_selected',
                'model': model
            }))
            return

        # Tangani pembaruan use_persona
        if use_persona is not None:
            has_messages = await self.has_messages()
            if not has_messages:
                await self.update_session_use_persona(use_persona)
                await self.send(text_data=json.dumps({
                    'type': 'session_info',
                    'use_persona': use_persona,
                    'disable_toggle': False
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Cannot change persona setting after messages exist'
                }))
                return

        # Proses pesan
        if message_content:
            self.response_text = ""
            await self.save_user_message(session_id, message_content)

            await self.channel_layer.group_send(self.room_group_name, {'type': 'assistant_response_start'})
            asyncio.create_task(self.process_streaming_response(message_content, session_id))

    async def process_streaming_response(self, query, session_id):
        try:
            retriever = DocumentRetriever()
            retrieved_docs = retriever.invoke(query)
            context = build_context(retrieved_docs)

            async def token_callback(token):
                self.response_text += token
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'assistant_response_chunk', 'message': token}
                )

            session = await self.get_session()
            full_response = await generate_streaming_response(
                query, context, self.memory, token_callback, session.id, self.user
            )

            await self.save_assistant_message(session_id, full_response)
            await self.channel_layer.group_send(self.room_group_name, {'type': 'assistant_response_end'})

            # After processing a message and saving it:
            has_messages = await self.has_messages()
            if has_messages:
                await self.send(text_data=json.dumps({
                    'type': 'session_info',
                    'use_persona': session.use_persona,
                    'disable_toggle': True,
                    'disable_model_select': True,
                    'session_id': self.session_id,
                    'selected_model': session.selected_model,
                }))
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
        
    async def load_initial_history(self):
        chat_history = await self.get_chat_history(self.session_id)
        for msg in chat_history:
            if msg["role"] == "user":
                self.memory.save_context({"input": msg["content"]}, {"output": ""})
            elif msg["role"] == "assistant":
                self.memory.save_context({"input": ""}, {"output": msg["content"]})

    @database_sync_to_async
    def save_user_message(self, session_id, content):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        Message.objects.create(session=session, role=Message.Role.USER, content=content)

    @database_sync_to_async
    def save_assistant_message(self, session_id, content):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        Message.objects.create(session=session, role=Message.Role.ASSISTANT, content=content)

    @database_sync_to_async
    def get_session(self):
        return ChatSession.objects.get(id=self.session_id, user=self.user)

    @database_sync_to_async
    def has_messages(self):
        session = ChatSession.objects.get(id=self.session_id, user=self.user)
        return session.messages.exists()

    @database_sync_to_async
    def update_session_use_persona(self, use_persona):
        session = ChatSession.objects.get(id=self.session_id, user=self.user)
        session.use_persona = use_persona
        session.save()

    @database_sync_to_async
    def get_chat_history(self, session_id):
        session = ChatSession.objects.get(id=session_id, user=self.user)
        messages = Message.objects.filter(session=session).order_by('timestamp')
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    @database_sync_to_async
    def update_session_model(self, model):
        session = ChatSession.objects.get(id=self.session_id, user=self.user)
        session.selected_model = model
        session.save()

    @database_sync_to_async
    def get_or_create_memory(self, session_id):
        memory = ConversationBufferMemory(return_messages=True)
        session = ChatSession.objects.get(id=session_id, user=self.user)
        messages = Message.objects.filter(session=session).order_by('timestamp')
        last_user_input = None
        for msg in messages:
            if msg.role == Message.Role.USER:
                last_user_input = msg.content
            elif msg.role == Message.Role.ASSISTANT and last_user_input:
                memory.save_context({"input": last_user_input}, {"output": msg.content})
                last_user_input = None
        return memory
    
