# Generated by Django 4.2.7 on 2023-11-21 14:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0027_alter_notification_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['date']},
        ),
    ]
