# Generated by Django 4.2.7 on 2023-11-22 12:12

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0044_alter_user_last_seen_alter_user_phonenumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2023, 11, 22, 12, 12, 56, 818391, tzinfo=datetime.timezone.utc)),
        ),
    ]
