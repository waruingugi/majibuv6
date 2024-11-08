# Generated by Django 5.0.6 on 2024-08-01 11:08

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0004_alter_result_exits_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="answer",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="choice",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="question",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="result",
            name="exits_at",
            field=models.DateTimeField(
                default=datetime.datetime(2024, 8, 1, 11, 38, 39, 506340),
                help_text="Time after which the session should be paired or refunded.",
            ),
        ),
        migrations.AlterField(
            model_name="result",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="useranswer",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
