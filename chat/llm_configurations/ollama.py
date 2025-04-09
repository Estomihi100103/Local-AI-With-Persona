from langchain_ollama import ChatOllama

def get_ollama_instance(callbacks=None):
    """Create and return an LLM instance with specified parameters."""
    print("Using Ollama Lokal ")
    return ChatOllama(
        model='qwen2.5-coder:0.5b',
        streaming=True,
        callbacks=callbacks,
    )