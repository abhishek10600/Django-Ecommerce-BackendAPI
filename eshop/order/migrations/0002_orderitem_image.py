# Generated by Django 5.0.6 on 2024-06-12 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='image',
            field=models.CharField(default='', max_length=500),
        ),
    ]