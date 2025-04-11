# personaai/chat/rag/graph.py
# File ini tidak digunakan lagi karena beralih ke ConversationBufferMemory.
# Simpan untuk referensi masa depan jika ingin kembali ke LangGraph.


# personaai/chat/rag/llm.py
async def generate_streaming_response(query, context, memory, token_callback, persona_prompt=""):
    llm = get_ollama_instance()
    prompt = create_conversation_prompt()
    history = memory.load_memory_variables({})["history"]
    # Tambahkan persona_prompt ke system template
    system_template = f"{persona_prompt}\nUse the following document as additional context to answer the question.\nHERE IS THE DOCUMENT:\n
    {context}"
    formatted_prompt = prompt.format_messages(query=query, context=system_template, history=history)
    full_response = ""
    async for chunk in llm.astream(formatted_prompt):
        if hasattr(chunk, 'content'):
            token = chunk.content
            full_response += token
            await token_callback(token)
    memory.save_context({"input": query}, {"output": full_response})
    return full_response