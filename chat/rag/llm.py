# personaai/chat/rag/llm.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from chat.llm_configurations.ollama import get_ollama_instance
from chat.llm_configurations.openai import get_openai_instance

def build_context(retrieved_docs):
    """Build context string from retrieved documents."""
    if not retrieved_docs:
        return "No context available."
    return "\n\n".join([doc.page_content for doc in retrieved_docs])


def create_conversation_prompt():
    system_template = """
    Use the following document as additional context to answer the question.
    IMPORTANT INSTRUCTIONS:
    1. Focus on accuracy.
    2. When giving examples, use the document as references if relevant.
    3. Do not mention that you used a "document" or "conversation history" in your answer.
    HERE IS THE DOCUMENT:
    {context}
    """
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="history"),  # Riwayat dari ConversationBufferMemory
        ("human", "{query}")
    ])

async def generate_streaming_response(query, context, memory, token_callback):
    # llm = get_ollama_instance()
    llm = get_openai_instance()
    prompt = create_conversation_prompt()

    # Muat riwayat dari memory
    history = memory.load_memory_variables({})["history"]

    # Format prompt dengan riwayat, query, dan context
    formatted_prompt = prompt.format_messages(query=query, context=context, history=history)
    print(f"Formatted prompt: {formatted_prompt}")

    # Streaming respons
    full_response = ""
    async for chunk in llm.astream(formatted_prompt):
        if hasattr(chunk, 'content'):
            token = chunk.content
            full_response += token
            await token_callback(token)

    # Simpan query dan respons ke memory
    memory.save_context({"input": query}, {"output": full_response})
    return full_response