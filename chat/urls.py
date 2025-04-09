from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('session/new/', views.create_session, name='create_session'),
    path('session/<int:session_id>/', views.chat_detail, name='chat_detail'),
]
