# Generated by Django 2.0.5 on 2018-07-16 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0006_customuser_friends'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='friends',
            field=models.TextField(blank=True, default=''),
        ),
    ]
