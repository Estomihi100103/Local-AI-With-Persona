# personaai/chat/rag/llm.py
import os
from typing import Dict, List, Any, Generator, Callable
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain.memory import ConversationBufferMemory
from langsmith import Client
from chat.llm_configurations.openai import get_openai_instance
from chat.llm_configurations.ollama import get_ollama_instance

from django.conf import settings
from functools import partial

# Set up LangSmith monitoring if API key is available
langsmith_client = None
if hasattr(settings, 'LANGCHAIN_API_KEY') and settings.LANGCHAIN_API_KEY:
    langsmith_client = Client(
        api_key=settings.LANGCHAIN_API_KEY,
    )

class StreamingCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for streaming tokens."""
    
    def __init__(self, token_callback):
        """Initialize with a callback function that will receive tokens."""
        self.token_callback = token_callback
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Send the token through the callback."""
        if self.token_callback:
            self.token_callback(token)











def create_response_generation_prompt():
    """Create and return the prompt template for response generation."""
    system_template = """
    You are a helpful AI assistant that responds to user queries with information from your knowledge and 
    the provided context from relevant documents. Always respond in a helpful, respectful manner.

    Use the following pieces of context to answer the user's question:
    {context}

    If the context doesn't contain relevant information, just use your general knowledge to answer.
    If you don't know the answer, just say that you don't know.
    """
    

    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", "Question: {query}")
    ])

# Standard response generation for Langgraph
def generate_langgraph_response(state: dict) -> dict:
    """
    Generates a response based on query and context for Langgraph.
    """
    # Use model GPT-4 for response generation
    # llm = get_openai_instance()
    
    # Create LLM Ollama instance
    llm = get_ollama_instance()

    # Prompt for response generation
    response_prompt = create_response_generation_prompt()

    # Execute chain
    query = state["original_query"]
    context = state.get("relevant_context", "No context available.")

    # Use invoke directly on llm
    response = llm.invoke(response_prompt.format_messages(
        query=query, 
        context=context
    ))

    # Update state
    return {**state, "response": response.content}

# Streaming version for use with WebSockets
def generate_streaming_response(state: dict, token_callback: Callable[[str], None]) -> dict:
    """
    Generates a streaming response, sending tokens through the callback function.
    
    Args:
        state: The current state dictionary
        token_callback: Function that will be called with each token
        
    Returns:
        Updated state with the full response
    """
    # Create a streaming handler
    handler = StreamingCallbackHandler(token_callback)
    
    # Create LLM with streaming enabled
    # llm = get_openai_instance(
    #     callbacks=[handler]
    # )
    
    # Create LLM Ollama instance
    llm = get_ollama_instance(
        callbacks=[handler]
    )
    
    # Prompt for response generation
    response_prompt = create_response_generation_prompt()
    
    # Get data from state
    query = state["original_query"]
    context = state.get("relevant_context", "No context available.")
    
    # Generate response with streaming
    full_response = ""
    for chunk in llm.stream(response_prompt.format_messages(
        query=query, 
        context=context
    )):
        if hasattr(chunk, 'content'):
            full_response += chunk.content or ""
    
    # Update state with the full response
    return {**state, "response": full_response}

# Async streaming version for WebSockets
async def generate_streaming_response_async(state: dict, token_callback: Callable[[str], None]) -> dict:
    """
    Async version of streaming response generation.
    
    Args:
        state: The current state dictionary
        token_callback: Async function that will be called with each token
        
    Returns:
        Updated state with the full response
    """
    # Create a streaming handler that calls the async callback
    class AsyncStreamingHandler(BaseCallbackHandler):
        async def on_llm_new_token(self, token: str, **kwargs) -> None:
            await token_callback(token)
    
    handler = AsyncStreamingHandler()
    
    # Create LLM with streaming enabled
    # llm = get_openai_instance(
    #     callbacks=[handler]
    # )
    
    #Cretae LLM Ollama instance
    llm = get_ollama_instance(
        callbacks=[handler]
    )
    
    # Prompt for response generation
    response_prompt = create_response_generation_prompt()
    
    # Get data from state
    query = state["original_query"]
    context = state.get("relevant_context", "No context available.")
    
    # Generate response with streaming
    full_response = ""
    async for chunk in llm.astream(response_prompt.format_messages(
        query=query, 
        context=context
    )):
        if hasattr(chunk, 'content'):
            full_response += chunk.content or ""
    
    # Update state with the full response
    return {**state, "response": full_response}