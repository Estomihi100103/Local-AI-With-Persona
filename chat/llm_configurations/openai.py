from django.conf import settings
from langchain_openai import ChatOpenAI

def get_openai_instance(callbacks=None):
    """Create and return an LLM instance with specified parameters."""
    return ChatOpenAI(
        model='chatgpt-4o-latest',
        openai_api_key=settings.OPENAI_API_KEY,
        streaming=True,
        callbacks=callbacks,
    )