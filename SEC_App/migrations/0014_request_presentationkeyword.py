# Generated by Django 3.2.4 on 2021-07-07 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SEC_App', '0013_auto_20210701_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='presentationkeyword',
            field=models.TextField(default=None),
        ),
    ]
