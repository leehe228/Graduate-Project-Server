from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health_check'),
    path('auth/register', views.register, name='register'),
    path('auth/login', views.login, name='login'),
    path('auth/user', views.get_user, name='get_user'),
    path('files/upload', views.upload_file, name='upload_file'),
    path('files/list', views.list_files, name='list_files'),
    path('files/delete', views.delete_file, name='delete_file'),
    path('chat/start', views.start_chat, name='start_chat'),
    path('chat/query', views.query_chat, name='query_chat'),
    path('chat/list', views.list_chats, name='list_chats'),
    path('chat/history', views.get_chat_history, name='get_chat_history'),
    path('chat/delete', views.delete_chat, name='delete_chat'),
    path('demo', views.chat_demo, name='chat_demo')
]
