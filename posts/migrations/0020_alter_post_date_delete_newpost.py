# Generated by Django 4.2.7 on 2023-11-17 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0019_post_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='date',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.DeleteModel(
            name='NewPost',
        ),
    ]