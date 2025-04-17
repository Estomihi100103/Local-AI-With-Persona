from langchain_ollama import ChatOllama

def get_ollama_instance(model='gemma3:1b', callbacks=None):
    """Create and return an LLM instance with specified parameters."""
    print(f"Using Ollama model: {model}")
    return ChatOllama(
        model=model,
        streaming=True,
        callbacks=callbacks,
    )
    
    # qwen2.5-coder:0.5b