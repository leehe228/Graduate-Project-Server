from django.contrib import admin
from .models import User, File, Chat, Message

# Register your models here.

admin.site.register(User)
admin.site.register(File)
admin.site.register(Chat)
admin.site.register(Message)
