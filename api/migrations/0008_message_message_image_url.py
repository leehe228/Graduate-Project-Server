# Generated by Django 5.2.1 on 2025-05-18 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_chat_file_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='message_image_url',
            field=models.CharField(default='', max_length=255),
        ),
    ]
