# Generated by Django 4.2.7 on 2023-11-11 23:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0009_alter_newpost_category_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='engagement',
            new_name='strength',
        ),
    ]
