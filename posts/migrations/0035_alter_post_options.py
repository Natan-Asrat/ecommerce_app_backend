# Generated by Django 4.2.7 on 2023-11-21 20:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0034_alter_post_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-date'], 'permissions': [('edit_and_add_posts_of_others', 'Can edit and add posts of others')]},
        ),
    ]