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
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    file_id = models.AutoField(primary_key=True) # incremental
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=32)
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.file_path
