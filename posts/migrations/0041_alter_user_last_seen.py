# Generated by Django 4.2.7 on 2023-11-22 10:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0040_user_last_seen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2023, 11, 22, 10, 29, 34, 8474, tzinfo=datetime.timezone.utc)),
        ),
    ]
