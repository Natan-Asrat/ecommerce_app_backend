# Generated by Django 4.2.7 on 2023-11-09 15:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_interaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='InteractionUserToPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strength', models.IntegerField(default=1)),
                ('last_updated_time_of_strength', models.DateField(auto_now=True)),
                ('strength_over_time', models.DecimalField(decimal_places=2, max_digits=10)),
                ('post_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='iicf_post', to='posts.post')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='iicf_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
