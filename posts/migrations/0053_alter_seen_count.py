# Generated by Django 3.2.23 on 2023-12-02 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0052_alter_ads_postid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seen',
            name='count',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
