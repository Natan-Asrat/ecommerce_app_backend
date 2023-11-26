# Generated by Django 4.2.7 on 2023-11-15 21:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_rename_strength_interactionusertocategory_strength_sum_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='nextIconAction',
            field=models.CharField(choices=[('D', 'detail'), ('L', 'link'), ('P', 'pay')], max_length=1),
        ),
        migrations.CreateModel(
            name='Recommended',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('tag', models.IntegerField()),
                ('rank', models.DecimalField(decimal_places=2, max_digits=10)),
                ('postId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.post')),
                ('userId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]