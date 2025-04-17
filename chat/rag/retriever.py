from typing import List, Optional, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document as LangChainDocument
from django.conf import settings
from documents.utils import get_chroma_collection
from documents.embedding_utils import get_embedding_model
from pydantic import Field
from langchain_community.vectorstores import Chroma

class DocumentRetriever(BaseRetriever):
    """Retriever that uses ChromaDB to retrieve document chunks based on embeddings."""
    n_results: int = Field(default=2, description="Number of results to return")
    vectorstore: Chroma = None 
    def __init__(self, n_results: int = 2):
        super().__init__()
        self.n_results = n_results
        self.tags = ["chroma", "document_retriever"]
        self._embeddings_model = get_embedding_model()
        
        # Buat instance Chroma dari LangChain
        self.vectorstore = Chroma(
            persist_directory=settings.VECTOR_STORE_PATH,
            embedding_function=self._embeddings_model,
            collection_name="personaai"
        )
    
    # Implementasi metode _invoke baru yang direkomendasikan LangChain
    def _invoke(self, query: str, **kwargs) -> List[LangChainDocument]:
        """New standard method to retrieve documents."""
        print(f"Query received: {query}")
        return self.get_relevant_documents(query, run_manager=kwargs.get("run_manager"))
        
    def get_relevant_documents(self, query: str, *, run_manager: Optional[Any] = None) -> List[LangChainDocument]:
        """Retrieve relevant document chunks for a query with similarity search."""
        try:
            # Menggunakan similarity_search dari LangChain
            documents = self.vectorstore.similarity_search_with_score(
                query=query,
                k=self.n_results
            )
            for doc, score in documents:
                doc.metadata["similarity_score"] = score
            
            result_docs = [doc for doc, _ in documents]
            return result_docs
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
            
    async def aget_relevant_documents(self, query: str, *, run_manager: Optional[Any] = None) -> List[LangChainDocument]:
        """Asynchronous version of get_relevant_documents."""
        return self.get_relevant_documents(query, run_manager=run_manager)
    
    # Implementasi metode _ainvoke untuk async (opsional)
    async def _ainvoke(self, query: str, **kwargs) -> List[LangChainDocument]:
        """New standard async method to retrieve documents."""
        return await self.aget_relevant_documents(query, run_manager=kwargs.get("run_manager"))