# Generated by Django 3.2.23 on 2024-08-10 06:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0070_alter_notification_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='backup_image',
            field=models.ImageField(blank=True, null=True, upload_to='backup/posts/'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='backup_verification_screenshot',
            field=models.ImageField(blank=True, null=True, upload_to='backup/transactions/'),
        ),
        migrations.AddField(
            model_name='user',
            name='backup_profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='backup/profile_pictures/'),
        ),
        migrations.AlterField(
            model_name='post',
            name='sellerId',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='posts', to=settings.AUTH_USER_MODEL),
        ),
    ]
