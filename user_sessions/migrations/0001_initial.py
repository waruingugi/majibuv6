# Generated by Django 5.0.6 on 2024-07-24 11:55

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PoolSessionStats",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("total_players", models.IntegerField(default=0, null=True)),
                ("_statistics", models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Sessions",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("category", models.CharField(max_length=255)),
                ("_questions", models.TextField(db_column="questions")),
            ],
        ),
        migrations.CreateModel(
            name="DuoSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("party_a", models.CharField(max_length=255)),
                ("party_b", models.CharField(max_length=255, null=True)),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="This is the Amount that was transacted.",
                        max_digits=10,
                        null=True,
                    ),
                ),
                ("status", models.CharField(max_length=255, null=True)),
                ("winner_id", models.CharField(max_length=255, null=True)),
                (
                    "session",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="user_sessions.sessions",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserSessionStats",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("total_wins", models.IntegerField(default=0)),
                ("total_losses", models.IntegerField(default=0)),
                ("sessions_played", models.IntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "abstract": False,
            },
        ),
    ]
