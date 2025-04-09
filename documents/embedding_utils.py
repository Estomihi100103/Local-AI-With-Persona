# personaai/documents/embedding_utils.py
from langchain_openai import OpenAIEmbeddings
from django.conf import settings
import chromadb


def get_embedding_model():
    """Returns a configured OpenAIEmbeddings instance."""
    return OpenAIEmbeddings(
        openai_api_key=settings.OPENAI_API_KEY,
        model="text-embedding-3-small"
    )
     
def get_chroma_collection():
    chroma_client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
    return chroma_client.get_or_create_collection(name="personaai")
