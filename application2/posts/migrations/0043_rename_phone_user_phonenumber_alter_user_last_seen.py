# Generated by Django 4.2.7 on 2023-11-22 12:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0042_alter_post_sellerid_alter_user_last_seen'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='phone',
            new_name='phoneNumber',
        ),
        migrations.AlterField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(default=datetime.datetime(2023, 11, 22, 12, 11, 34, 327833, tzinfo=datetime.timezone.utc)),
        ),
    ]
