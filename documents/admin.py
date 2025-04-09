from django.contrib import admin
from .models import DocumentChunk, Document

# Register your models here.
admin.site.register(Document)

class DocumentChunkAdmin(admin.ModelAdmin):
    # Langsung tambahkan field dari model yang diinginkan
    list_display = ['document', 'chunk_index', 'embedding_id']

    # Anda juga bisa menambahkan fungsi custom untuk menampilkan kolom terkait (optional)
    @admin.display(description='Document ID')
    def document_id(self, obj):
        return obj.document.id  # Menampilkan ID dari Document yang terkait

    @admin.display(description='Embedding ID')
    def embedding_id(self, obj):
        return obj.embedding_id

admin.site.register(DocumentChunk, DocumentChunkAdmin)
