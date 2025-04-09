import os

# Pastikan ini ada di awal sekali, sebelum impor lainnya
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django
from dotenv import load_dotenv

# Inisialisasi Django secara eksplisit
django.setup()
load_dotenv()

# Impor setelah setup Django
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})