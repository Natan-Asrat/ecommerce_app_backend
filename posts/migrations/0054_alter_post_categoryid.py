# Generated by Django 4.2.7 on 2023-12-08 12:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0053_alter_seen_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='categoryId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts_in_category', to='posts.category'),
        ),
    ]