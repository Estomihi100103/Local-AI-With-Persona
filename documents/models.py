# personaai/documents/models.py
from django.db import models
from django.contrib.auth.models import User
from .embedding_utils import get_chroma_collection


class Document(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='documents/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField()
    embedding_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
    
    def get_embedding_vector(self):
        try:
            collection = get_chroma_collection()
            data = collection.get(ids=[self.embedding_id], include=["embeddings"])
            return data["embeddings"][0] if data["embeddings"] else None
        except Exception as e:
            return None
    
    class Meta:
        ordering = ['chunk_index']