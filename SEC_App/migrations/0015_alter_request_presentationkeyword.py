# Generated by Django 3.2.4 on 2021-07-07 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SEC_App', '0014_request_presentationkeyword'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='presentationkeyword',
            field=models.TextField(default=None, null=True),
        ),
    ]
