from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from chat.models import ChatSession
from accounts.models import UserProfile  

@database_sync_to_async
def get_persona(user):
    """Mengambil persona pengguna dari basis data."""
    try:
        return user.userprofile.persona.description
    except UserProfile.DoesNotExist:
        return None

@database_sync_to_async
def get_use_persona(session_id):
    """Mengambil status penggunaan persona dari sesi chat."""
    try:
        session = ChatSession.objects.get(id=session_id)
        return session.use_persona
    except ChatSession.DoesNotExist:
        return None