# Generated by Django 4.2.7 on 2023-11-22 15:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0048_alter_category_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interactionusertocategory',
            name='category_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interaction', to='posts.category'),
        ),
    ]
