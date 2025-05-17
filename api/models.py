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
