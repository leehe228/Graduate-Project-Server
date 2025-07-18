from django.db import models
from django.utils import timezone

# Create your models here.

class User(models.Model):
    user_id = models.CharField(max_length=32, unique=True, primary_key=True)
    user_email = models.EmailField(max_length=255, unique=True)
    user_password = models.CharField(max_length=32)
    user_name = models.CharField(max_length=32)
    user_category = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user_id


class File(models.Model):
    class FileProcessingStatus(models.IntegerChoices):
        PENDING = 1, 'Pending'
        PROCESSING = 2, 'Processing'
        COMPLETED = 3, 'Completed'
        FAILED = 4, 'Failed'

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    file_id = models.AutoField(primary_key=True) # incremental
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=32)
    file_path = models.CharField(max_length=255)
    file_sqlpath = models.CharField(default="", max_length=255)
    file_schema = models.TextField(default="")
    file_processed = models.IntegerField(choices=FileProcessingStatus.choices, default=FileProcessingStatus.PENDING)
    file_error = models.TextField(default="")
    file_business_category = models.CharField(max_length=32, default="default")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.file_path


class Chat(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_id = models.AutoField(primary_key=True) # incremental
    chat_title = models.CharField(default="", max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    file_id = models.ForeignKey(File, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.chat_title


class Message(models.Model):
    class MessageRole(models.IntegerChoices):
        SYSTEM = 1, 'System'
        ASSISTANT = 2, 'Assistant'
        USER = 3, 'User'
        INTERNAL = 4, 'Internal'

    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE)
    message_id = models.AutoField(primary_key=True) # incremental
    message_text = models.TextField(max_length=4096)
    message_role = models.IntegerField(choices=MessageRole.choices, default=MessageRole.USER)
    message_image_url = models.CharField(max_length=255, null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.message_text
