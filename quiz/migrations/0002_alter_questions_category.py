# Generated by Django 5.0.6 on 2024-07-24 12:07

import commons.constants
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="questions",
            name="category",
            field=models.CharField(
                choices=[
                    (commons.constants.SessionCategories["FOOTBALL"], "FOOTBALL"),
                    (commons.constants.SessionCategories["BIBLE"], "BIBLE"),
                ],
                max_length=255,
            ),
        ),
    ]
