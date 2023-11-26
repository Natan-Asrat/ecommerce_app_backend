# Generated by Django 4.2.7 on 2023-11-11 23:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_rename_engagement_post_strength'),
    ]

    operations = [
        migrations.RenameField(
            model_name='interactionusertocategory',
            old_name='strength',
            new_name='strength_sum',
        ),
        migrations.RenameField(
            model_name='interactionusertopost',
            old_name='strength',
            new_name='strength_sum',
        ),
        migrations.RenameField(
            model_name='interactionusertouser',
            old_name='strength',
            new_name='strength_sum',
        ),
        migrations.AlterField(
            model_name='post',
            name='strength',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]