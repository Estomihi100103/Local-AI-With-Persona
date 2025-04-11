from langchain_ollama import ChatOllama

def get_ollama_instance(callbacks=None):
    """Create and return an LLM instance with specified parameters."""
    print("Using Ollama Lokal ")
    return ChatOllama(
        model='gemma3:1b',
        streaming=True,
        callbacks=callbacks,
    )
    
    # qwen2.5-coder:0.5b