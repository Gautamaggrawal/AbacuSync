# Generated by Django 5.1.7 on 2025-03-25 11:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0002_alter_student_ci_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="studentlevelhistory",
            name="changed_by",
            field=models.ForeignKey(
                blank=True,
                help_text="User who changed the level",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="level_changes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
