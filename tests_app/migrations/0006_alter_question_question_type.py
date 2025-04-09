# Generated by Django 5.1.7 on 2025-03-26 21:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests_app", "0005_alter_question_question_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="question_type",
            field=models.CharField(
                choices=[
                    ("plus", "Plus/Addition"),
                    ("multiply", "Multiply"),
                    ("divide", "Divide/Division"),
                ],
                default="multiply",
                max_length=20,
                verbose_name="question type",
            ),
        ),
    ]
