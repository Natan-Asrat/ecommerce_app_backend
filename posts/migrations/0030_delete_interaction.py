# Generated by Django 4.2.7 on 2023-11-21 14:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0029_alter_notification_options'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Interaction',
        ),
    ]
