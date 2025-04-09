# Generated by Django 5.1.7 on 2025-03-08 14:07

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("centres", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Level",
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
                ("name", models.CharField(max_length=50, verbose_name="name")),
                (
                    "description",
                    models.TextField(
                        blank=True, null=True, verbose_name="description"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="created at"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="updated at"
                    ),
                ),
            ],
            options={
                "verbose_name": "level",
                "verbose_name_plural": "levels",
            },
        ),
        migrations.CreateModel(
            name="Student",
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
                ("dob", models.DateField(verbose_name="date of birth")),
                (
                    "gender",
                    models.CharField(
                        choices=[
                            ("M", "Male"),
                            ("F", "Female"),
                            ("O", "Other"),
                        ],
                        max_length=1,
                        verbose_name="gender",
                    ),
                ),
                (
                    "level_start_date",
                    models.DateField(verbose_name="level start date"),
                ),
                (
                    "level_completion_date",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="level completion date",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="active"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="created at"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="updated at"
                    ),
                ),
                (
                    "centre",
                    models.ForeignKey(
                        help_text="Centre this student belongs to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="students",
                        to="centres.centre",
                    ),
                ),
                (
                    "ci",
                    models.ForeignKey(
                        help_text="CI assigned to this student",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="students",
                        to="centres.ci",
                    ),
                ),
                (
                    "current_level",
                    models.ForeignKey(
                        help_text="Current level of the student",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="students",
                        to="students.level",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        help_text="User account associated with this student",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "student",
                "verbose_name_plural": "students",
            },
        ),
        migrations.CreateModel(
            name="StudentLevelHistory",
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
                ("start_date", models.DateField(verbose_name="start date")),
                (
                    "completion_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="completion date"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="created at"
                    ),
                ),
                (
                    "changed_by",
                    models.ForeignKey(
                        help_text="User who changed the level",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="level_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "new_level",
                    models.ForeignKey(
                        help_text="New level of the student",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="new_students",
                        to="students.level",
                    ),
                ),
                (
                    "previous_level",
                    models.ForeignKey(
                        blank=True,
                        help_text="Previous level of the student",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="previous_students",
                        to="students.level",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        help_text="Student whose level is being changed",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="level_history",
                        to="students.student",
                    ),
                ),
            ],
            options={
                "verbose_name": "student level history",
                "verbose_name_plural": "student level histories",
            },
        ),
        migrations.AddIndex(
            model_name="student",
            index=models.Index(
                fields=["is_active"], name="students_st_is_acti_c00e81_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="student",
            index=models.Index(
                fields=["centre", "is_active"],
                name="students_st_centre__ba03cc_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="studentlevelhistory",
            index=models.Index(
                fields=["student", "created_at"],
                name="students_st_student_c54b2d_idx",
            ),
        ),
    ]
