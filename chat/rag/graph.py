# personaai/chat/rag/graph.py
from typing import Dict, List, Tuple, Any, TypedDict, Annotated
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from .retriever import DocumentRetriever
from django.conf import settings
from .llm import generate_langgraph_response
from chat.llm_configurations.openai import get_openai_instance
from chat.llm_configurations.ollama import get_ollama_instance

# Definisi struktur State untuk Langgraph
class RAGState(TypedDict):
    """Struktur state untuk RAG graph."""
    original_query: str  # Query asli dari pengguna
    refined_query: str   # Query yang telah diperbaiki/diproses
    retrieved_documents: List[Document]  # Dokumen yang diambil
    relevant_context: str  # Konteks relevan yang diambil dari dokumen
    response: str  # Respons akhir
    chat_history: List[Dict]  # Riwayat chat


# 1. Node untuk Query Preprocessing/Refinement
def query_preprocessing(state: RAGState) -> RAGState:
    """
    Memproses dan memperbaiki query dari pengguna menggunakan LLM.
    """
    # llm = get_openai_instance()
    
    llm = get_ollama_instance()
    
    # Prompt untuk memperbaiki query
    query_processing_prompt = ChatPromptTemplate.from_messages([
        ("system", "Anda adalah asisten yang membantu memperbaiki query pencarian. "
                  "Tugas Anda adalah memahami maksud dari query dan mengubahnya menjadi "
                  "query yang lebih efektif untuk pencarian informasi."),
        ("user", "Berikan query yang telah dioptimalkan berdasarkan: {original_query}")
    ])
    
    # Chain untuk memproses query
    query_chain = query_processing_prompt | llm | StrOutputParser()
    
    # Ambil riwayat chat jika ada untuk konteks
    chat_history = state.get("chat_history", [])
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-3:]])
    
    # Eksekusi chain
    refined_query = query_chain.invoke({
        "original_query": state["original_query"],
        "context": context
    })
    
    # Update state
    return {**state, "refined_query": refined_query}


# 2. Node untuk Document Retrieval
def retrieve_documents(state: RAGState) -> RAGState:
    """
    Mengambil dokumen relevan menggunakan DocumentRetriever.
    """
    retriever = DocumentRetriever()
    query = state["original_query"]
    # Ambil dokumen
    retrieved_docs = retriever.invoke(query)
    
    # print ke terminal hasil dari retriever
    # print("Hasil dari retriever:", retrieved_docs)
    
    # Update state
    return {**state, "retrieved_documents": retrieved_docs}


# 3. Node untuk Document Filtering/Reranking
def filter_documents(state: RAGState) -> RAGState:
    """
    Memfilter dan menyusun ulang dokumen berdasarkan relevansi yang lebih mendalam.
    """
    # llm = get_openai_instance()
    
    llm = get_ollama_instance()
    
    
    # Jika tidak ada dokumen yang diambil, skip proses ini
    if not state.get("retrieved_documents"):
        return state
    
    docs = state["retrieved_documents"]
    query = state.get("refined_query", state["original_query"])
    
    # Buat prompt untuk evaluasi relevansi
    reranking_prompt = ChatPromptTemplate.from_messages([
        ("system", "Evaluasi relevansi tiap dokumen terhadap query. "
                  "Berikan skor 0-10 untuk setiap dokumen, dengan penjelasan singkat."),
        ("user", "Query: {query}\n\nDokumen: {document}")
    ])
    
    # Evaluasi dan skor setiap dokumen
    scored_docs = []
    for doc in docs:
        result = (reranking_prompt | llm | StrOutputParser()).invoke({
            "query": query,
            "document": doc.page_content
        })
        
        # Coba ekstrak skor dari hasil
        try:
            # Ambil angka pertama dalam teks sebagai skor
            import re
            score_match = re.search(r'\b([0-9]|10)\b', result)
            score = int(score_match.group(1)) if score_match else 0
        except:
            score = 0
            
        scored_docs.append((doc, score))
    
    # Urutkan dokumen berdasarkan skor
    sorted_docs = [doc for doc, _ in sorted(scored_docs, key=lambda x: x[1], reverse=True)]
    
    # Batasi jumlah dokumen jika terlalu banyak
    filtered_docs = sorted_docs[:3]  # Ambil 3 dokumen teratas
    
    # Update state
    return {**state, "retrieved_documents": filtered_docs}


# 4. Node untuk Context Building
def build_context(state: RAGState) -> RAGState:
    """
    Mengubah dokumen yang diambil menjadi konteks yang terstruktur.
    """
    # Jika tidak ada dokumen yang diambil, buat konteks kosong
    if not state.get("retrieved_documents"):
        return {**state, "relevant_context": ""}
    
    docs = state["retrieved_documents"]
    
    # Gabungkan konten dokumen dengan format yang baik
    formatted_context = ""
    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        chunk_index = metadata.get("chunk_index", "unknown")
        document_id = metadata.get("document_id", "unknown")
        
        formatted_context += f"--- DOKUMEN {i} (ID: {document_id}, Chunk: {chunk_index}) ---\n"
        formatted_context += doc.page_content + "\n\n"
    
    # Update state
    return {**state, "relevant_context": formatted_context}


# 5. Node untuk Response Generation
def generate_response(state: RAGState) -> RAGState:
    """
    Menghasilkan respons berdasarkan query dan konteks.
    """
    return generate_langgraph_response(state)

# 6. Node untuk Feedback dan Evaluasi (opsional)
def evaluate_response(state: RAGState) -> RAGState:
    """
    Mengevaluasi respons dan menentukan apakah perlu iterasi lebih lanjut.
    """
    # Implementasi sederhana: selalu selesaikan proses
    return {**state, "decision": "finalize"}


# 7. Definisi Graph
def create_rag_graph() -> StateGraph:
    """
    Membuat graph alur kerja RAG.
    """
    # Inisialisasi graph
    graph = StateGraph(RAGState)
    
    # Tambahkan node
    # graph.add_node("query_preprocessing", query_preprocessing)
    graph.add_node("retrieve_documents", retrieve_documents)
    # graph.add_node("filter_documents", filter_documents)
    graph.add_node("build_context", build_context)
    graph.add_node("generate_response", generate_response)
    # graph.add_node("evaluate_response", evaluate_response)
    
    # Definisikan edges (alur kerja)
    # graph.add_edge("query_preprocessing", "retrieve_documents")
    # graph.add_edge("retrieve_documents", "filter_documents")
    # graph.add_edge("filter_documents", "build_context")
    # graph.add_edge("build_context", "generate_response")
    # graph.add_edge("generate_response", "evaluate_response")
    
    
    graph.add_edge("retrieve_documents", "build_context") 
    graph.add_edge("build_context", "generate_response")
    
    # Definisikan conditional edges
    # graph.add_conditional_edges(
    #     "evaluate_response",
    #     lambda state: state["decision"],
    #     {
    #         "iterate": "query_preprocessing",  # Kembali ke awal jika perlu iterasi
    #         "finalize": END  # Selesai jika tidak perlu iterasi
    #     }
    # )
    
    # Set node awal
    # graph.set_entry_point("query_preprocessing")
    graph.set_entry_point("retrieve_documents")
    
    return graph


# 8. Fungsi untuk memanggil RAG Graph
def process_rag_query(
    query: str, 
    chat_history: List[Dict] = None
) -> Dict:
    """
    Fungsi utama untuk memproses query menggunakan RAG graph.
    
    Args:
        query: Query dari pengguna
        chat_history: Riwayat chat sebelumnya
    
    Returns:
        Dictionary berisi respons dan informasi terkait
    """
    # Inisialisasi state awal
    initial_state = RAGState(
        original_query=query,
        refined_query="",
        retrieved_documents=[],
        relevant_context="",
        response="",
        chat_history=chat_history or []
    )
    
    # Buat dan jalankan graph
    graph = create_rag_graph().compile()
    final_state = graph.invoke(initial_state)
    
    # Tambahkan interaksi ini ke riwayat chat
    updated_history = final_state.get("chat_history", []).copy()
    updated_history.append({"role": "user", "content": query})
    updated_history.append({"role": "assistant", "content": final_state["response"]})
    
    # Kembalikan hasil
    return {
        "query": query,
        "refined_query": final_state.get("refined_query", ""),
        "response": final_state["response"],
        "context_used": final_state.get("relevant_context", ""),
        "chat_history": updated_history
    }