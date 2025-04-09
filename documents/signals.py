from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Document, DocumentChunk
from .utils import process_document


@receiver(post_save, sender=Document)
def process_document_after_save(sender, instance, created, **kwargs):
    """
    Signal to process the document after it is saved.
    """
    if created and not instance.processed:
        process_document(instance)
        instance.processed = True
        instance.save()