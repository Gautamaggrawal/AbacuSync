# Generated by Django 5.1.7 on 2025-04-28 09:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0003_level_is_approved"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="level",
            name="is_approved",
        ),
        migrations.AddField(
            model_name="student",
            name="is_approved",
            field=models.BooleanField(default=False),
        ),
    ]
