# Generated by Django 5.0.6 on 2024-07-18 16:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "notifications",
            "0003_rename_show_in_app_notification_is_visible_in_app_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="is_visible_in_app",
        ),
    ]