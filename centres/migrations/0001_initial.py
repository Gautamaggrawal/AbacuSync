# Generated by Django 5.1.7 on 2025-03-08 13:59

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
            name="Centre",
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
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="UUID",
                    ),
                ),
                ("centre_name", models.CharField(max_length=100)),
                ("franchisee_name", models.CharField(max_length=100)),
                ("area", models.CharField(max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="centre_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "centre",
                "verbose_name_plural": "centres",
            },
        ),
        migrations.CreateModel(
            name="CI",
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
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="UUID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated at"),
                ),
                (
                    "centre",
                    models.ForeignKey(
                        help_text="Centre this CI belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cis",
                        to="centres.centre",
                    ),
                ),
            ],
            options={
                "verbose_name": "CI",
                "verbose_name_plural": "CIs",
            },
        ),
        migrations.AddIndex(
            model_name="centre",
            index=models.Index(
                fields=["is_active"], name="centres_cen_is_acti_3ed12d_idx"
            ),
        ),
    ]
