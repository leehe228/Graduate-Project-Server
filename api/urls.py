from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health_check'),
    path('auth/register', views.register, name='register'),
    path('auth/login', views.login, name='login'),
    path('auth/user', views.get_user, name='get_user'),
    path('files/upload', views.upload_file, name='upload_file'),
    path('files/list', views.list_files, name='list_files'),
]
