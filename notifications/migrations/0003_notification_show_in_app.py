# Generated by Django 5.0.6 on 2024-07-17 16:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_remove_notification_phone_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="show_in_app",
            field=models.BooleanField(default=True),
        ),
    ]
