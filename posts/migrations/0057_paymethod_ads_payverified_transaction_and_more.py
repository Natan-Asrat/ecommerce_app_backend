# Generated by Django 4.2.7 on 2023-12-28 21:47

import cloudinary.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0056_alter_ads_categoryid'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayMethod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('image', cloudinary.models.CloudinaryField(max_length=255, verbose_name='image')),
                ('isVirtualCurrency', models.BooleanField(default=False)),
                ('hasQRCode', models.BooleanField(default=False)),
                ('hasLink', models.BooleanField(default=False)),
                ('hasAccountNumber', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='ads',
            name='payVerified',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('currency', models.CharField(blank=True, choices=[('Br', 'Birr')], max_length=5, null=True)),
                ('usedVirtualCurrency', models.BooleanField(blank=True, default=False, null=True)),
                ('payVerified', models.BooleanField(blank=True, default=False, null=True)),
                ('title', models.CharField(max_length=100)),
                ('trueForDepositFalseForWithdraw', models.BooleanField(default=True)),
                ('rejected', models.BooleanField(blank=True, default=False, null=True)),
                ('verificationScreenshot', cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name='image')),
                ('issuedBy', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='byUser', to=settings.AUTH_USER_MODEL)),
                ('issuedFor', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='forUser', to=settings.AUTH_USER_MODEL)),
                ('payMethod', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='posts.paymethod')),
            ],
        ),
        migrations.AddField(
            model_name='ads',
            name='transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='posts.transaction'),
        ),
    ]