# Generated by Django 4.2.7 on 2023-11-20 18:27

import cloudinary.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0022_rename_strength_post_engagement_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interaction',
            name='last_updated_time_of_strength',
        ),
        migrations.AddField(
            model_name='user',
            name='profilePicture',
            field=cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name='image'),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', cloudinary.models.CloudinaryField(max_length=255, verbose_name='image')),
                ('order', models.PositiveIntegerField(default=1)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postImage', to='posts.post')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
