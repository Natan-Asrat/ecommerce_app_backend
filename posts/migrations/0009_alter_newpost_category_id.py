# Generated by Django 4.2.7 on 2023-11-10 21:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_newpost_category_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newpost',
            name='category_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.category'),
        ),
    ]
