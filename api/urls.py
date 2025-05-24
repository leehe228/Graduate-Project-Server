from django.urls import path
from . import views

urlpatterns = [
    path('api/health', views.health_check, name='health_check'),
    path('api/auth/register', views.register, name='register'),
    path('api/auth/login', views.login, name='login'),
    path('api/auth/user', views.get_user, name='get_user'),
    path('api/files/upload', views.upload_file, name='upload_file'),
    path('api/files/list', views.list_files, name='list_files'),
    path('api/files/delete', views.delete_file, name='delete_file'),
    path('api/chat/start', views.start_chat, name='start_chat'),
    path('api/chat/query', views.query_chat, name='query_chat'),
    path('api/chat/list', views.list_chats, name='list_chats'),
    path('api/chat/history', views.get_chat_history, name='get_chat_history'),
    path('api/chat/delete', views.delete_chat, name='delete_chat'),
    path('demo/', views.chat_demo, name='chat_demo')
]
