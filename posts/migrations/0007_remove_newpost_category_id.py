# Generated by Django 4.2.7 on 2023-11-10 21:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_alter_associationcategorytoseller_seller_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newpost',
            name='category_id',
        ),
    ]
