# personaai/chat/rag/llm.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from chat.llm_configurations.ollama import get_ollama_instance
from chat.llm_configurations.openai import get_openai_instance
from .persona import get_persona, get_use_persona
from channels.db import database_sync_to_async
from chat.models import ChatSession

def build_context(retrieved_docs):
    """Build context string from retrieved documents."""
    if not retrieved_docs:
        return "No context available."
    return "\n\n".join([doc.page_content for doc in retrieved_docs])

    
def create_conversation_prompt(context: str):
    system_template = """
    Kamu adalah asisten AI yang memberikan jawaban akurat dan relevan kepada pengguna.
    """.strip()
    
    human_context_template = """
    Use the following document as additional context to answer the question.
    IMPORTANT INSTRUCTIONS:
    1. Focus on accuracy.
    2. When giving examples, use the document as references if relevant.
    3. Do not mention that you used a "document" or "conversation history" in your answer.
    HERE IS THE DOCUMENT:\n\n
    
    {context}""".strip()
    
    human_question_template = "{query}"
    
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="history"),
        ("human", human_context_template),
        ("human", human_question_template)
    ])
    
    
def create_conversation_prompt_with_persona(context, user_persona):
    system_template = f"""
    Kamu adalah asisten AI dengan persona berikut:
    
    {user_persona}
    """
    
    human_template_context = """
    Use the following document as additional context to answer the question.
    IMPORTANT INSTRUCTIONS:
    1. Focus on accuracy.
    2. When giving examples, use the document as references if relevant.
    3. Do not mention that you used a "document" or "conversation history" in your answer.
    HERE IS THE DOCUMENT:\n\n
    
    {context}"""
    
    human_template_question = "{query}"
    
    return ChatPromptTemplate.from_messages([
        ("system", system_template.strip()),
        MessagesPlaceholder(variable_name="history"),
        ("human", human_template_context.strip()),
        ("human", human_template_question.strip())
    ])
    
@database_sync_to_async
def get_session_model(session_id):
    """Retrieve the selecttted model from session"""
    session = ChatSession.objects.get(id=session_id)
    return session.selected_model
    
async def generate_streaming_response(query, context, memory, token_callback, session_id, user):
    selected_model= await get_session_model(session_id)
    
    llm = get_ollama_instance(model=selected_model)
    print(f"Selected model: {selected_model}")
    
    # llm = get_openai_instance()
    use_persona = await get_use_persona(session_id)
    
    if use_persona and user:
        user_persona = await get_persona(user)
        prompt = create_conversation_prompt_with_persona(context, user_persona)
    else:
        prompt = create_conversation_prompt(context)


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