from datetime import timedelta

import pandas as pd
from django.db.models import Count, Max, Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from students.models import Level
from tests_app.models import (
    Question,
    StudentAnswer,
    StudentTest,
    Test,
    TestSection,
)

from .utils import AnswerEvaluator


class ExcelUploadSerializer(serializers.Serializer):
    """Optimized Serializer for handling Excel file uploads"""

    file = serializers.FileField()
    level_id = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Level.objects.all(),
    )
    title = serializers.CharField(max_length=200)
    section_type = serializers.CharField(max_length=10)

    def validate(self, data):
        """Improved file validation with more robust checks"""
        file = data.get("file")
        if not file:
            raise serializers.ValidationError("No file was uploaded")

        # Use a more comprehensive file extension check
        valid_extensions = (".xlsx", ".xls", ".xlsm")
        if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError(
                f"File must be one of: {', '.join(valid_extensions)}"
            )

        if data.get("section_type") == "ADD":
            try:
                # Use context manager for file handling
                with pd.ExcelFile(file) as xls:
                    df = pd.read_excel(xls)

                # More flexible column validation
                required_columns = ["No."]
                missing_columns = [
                    col for col in required_columns if col not in df.columns
                ]
                if missing_columns:
                    raise serializers.ValidationError(
                        f"Missing required columns: {', '.join(missing_columns)}"
                    )
                return data

            except Exception as e:
                raise serializers.ValidationError(
                    f"Error processing file: {str(e)}"
                )
        return data

    def create(self, validated_data):
        """Refactored method with improved performance and readability"""
        file = validated_data["file"]
        level_id = validated_data["level_id"]
        title = validated_data["title"]
        section_type = validated_data["section_type"]

        # Use context manager for file handling
        with pd.ExcelFile(file) as xls:
            df = pd.read_excel(xls, index_col=0)

        # Create test with a single database query
        test = Test.objects.create(title=title, level=level_id)

        # More efficient section order calculation
        max_order = test.sections.aggregate(Max("order"))["order__max"] or 0
        section = TestSection.objects.create(
            test=test, section_type=section_type, order=max_order + 1
        )

        # Separate methods for different section types
        if section_type == "MUL_DIV":
            self._create_mul_div_questions(section, df)
        else:
            self._create_addition_questions(section, df)

        return test

    def _create_mul_div_questions(self, section, df):
        """Create multiplication and division questions"""
        for i, row in df.iterrows():
            values = [val for val in row.dropna().tolist()]
            if not values or len(values) < 3:
                continue

            question_type = (
                Question.QuestionType.MULTIPLY
                if values[1] in ["x", "X", "*"]
                else Question.QuestionType.DIVIDE
                if values[1] in ["÷", "/"]
                else None
            )

            if question_type:
                Question.objects.create(
                    section=section,
                    text=str([values[0], values[2]]),
                    order=i,
                    marks=1,
                    question_type=question_type,
                )

    def _create_addition_questions(self, section, df):
        """Create addition questions"""
        # Remove empty columns and the 'ans' column
        df = df.dropna(axis=1, how="all")
        df = df[[col for col in df.columns if col != "ans"]]

        for idx, col in enumerate(df.columns, 1):
            values = df[col].tolist()

            # Remove NaN values and convert to integers
            calculation_values = [
                int(val) for val in values[:-1] if pd.notna(val)
            ]

            if calculation_values:
                Question.objects.create(
                    section=section,
                    text=str(calculation_values),
                    order=idx,
                    marks=1,
                    question_type=Question.QuestionType.PLUS,
                )


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["uuid", "text", "order", "marks", "question_type"]


class TestSectionSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = TestSection
        fields = ["uuid", "section_type", "order", "questions"]


class TestSerializer(serializers.ModelSerializer):
    sections = TestSectionSerializer(many=True, read_only=True)
    duration_remaining = serializers.SerializerMethodField()
    level_uuid = serializers.UUIDField(source="level.uuid")

    class Meta:
        model = Test
        fields = [
            "uuid",
            "title",
            "level",
            "level_uuid",
            "duration_minutes",
            "sections",
            "duration_remaining",
            "due_date",
            "created_at",
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_duration_remaining(self, obj):
        """Get remaining duration in seconds for the current test session"""
        student_test = self.context.get("student_test")
        if student_test and student_test.session:
            return student_test.session.remaining_time_seconds
        return obj.duration_minutes * 60


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = [
            "uuid",
            "question",
            "answer_text",
            "is_correct",
            "marks_obtained",
        ]
        read_only_fields = ["is_correct", "marks_obtained"]


class StudentTestSerializer(serializers.ModelSerializer):
    test = TestSerializer(read_only=True)
    remaining_duration = serializers.SerializerMethodField()
    answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = StudentTest
        fields = [
            "uuid",
            "test",
            "status",
            "start_time",
            "end_time",
            "remaining_duration",
            "answers",
        ]
        read_only_fields = ["uuid", "status", "start_time", "end_time"]

    def get_remaining_duration(self, obj):
        """Get remaining duration in seconds"""
        if obj.status not in ["IN_PROGRESS", "INTERRUPTED"]:
            return 0

        session = obj.session
        if not session:
            return 0

        return max(0, session.remaining_time_seconds)

    def to_representation(self, instance):
        """Add test context for duration calculation"""
        representation = super().to_representation(instance)
        representation["test"] = TestSerializer(
            instance.test, context={"student_test": instance}
        ).data
        return representation


class AnswerSubmissionSerializer(serializers.Serializer):
    """Serializer for a single answer submission"""

    question = serializers.UUIDField()
    answer_text = serializers.CharField()


class TestSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting test answers"""

    answers = serializers.ListField(child=AnswerSubmissionSerializer())


class SimplifiedAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text")
    question_order = serializers.IntegerField(source="question.order")
    correct_answer_value = serializers.SerializerMethodField()

    class Meta:
        model = StudentAnswer
        fields = [
            "question_text",
            "question_order",
            "answer_text",
            "is_correct",
            "marks_obtained",
            "correct_answer_value",
        ]

    def get_correct_answer_value(self, obj):
        """Get correct answer based on question type"""
        expected_answer = AnswerEvaluator.calculate_answer(obj.question)
        return AnswerEvaluator.format_answer(
            expected_answer, obj.question.question_type
        )


class EnhancedTestResultSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    marks_obtained = serializers.SerializerMethodField()
    correct_answers = serializers.SerializerMethodField()
    incorrect_answers = serializers.SerializerMethodField()
    accuracy_percentage = serializers.SerializerMethodField()
    completion_time = serializers.SerializerMethodField()
    total_attempted = serializers.SerializerMethodField()
    answers = SimplifiedAnswerSerializer(source="answers.all", many=True)

    class Meta:
        model = StudentTest
        fields = [
            "uuid",
            "status",
            "start_time",
            "end_time",
            "total_questions",
            "total_attempted",
            "total_marks",
            "marks_obtained",
            "correct_answers",
            "incorrect_answers",
            "accuracy_percentage",
            "completion_time",
            "answers",
        ]

    def get_total_questions(self, obj):
        """Get total number of questions across all sections"""
        return (
            obj.test.sections.annotate(
                question_count=Count("questions")
            ).aggregate(total=Sum("question_count"))["total"]
            or 0
        )

    def get_total_attempted(self, obj):
        """Get total number of attempted questions"""
        return obj.answers.count()

    def get_total_marks(self, obj):
        return (
            obj.test.sections.aggregate(total=Sum("questions__marks"))["total"]
            or 0
        )

    def get_marks_obtained(self, obj):
        return obj.answers.aggregate(total=Sum("marks_obtained"))["total"] or 0

    def get_correct_answers(self, obj):
        return obj.answers.filter(is_correct=True).count()

    def get_incorrect_answers(self, obj):
        return obj.answers.filter(is_correct=False).count()

    def get_accuracy_percentage(self, obj):
        attempted = self.get_total_attempted(obj)
        if attempted == 0:
            return 0
        correct = self.get_correct_answers(obj)
        return round((correct / attempted) * 100, 2)

    def get_completion_time(self, obj):
        if obj.start_time and obj.end_time:
            duration = (obj.end_time - obj.start_time).total_seconds()
            return {
                "seconds": int(duration),
                "formatted": str(timedelta(seconds=int(duration))),
            }
        return None


class TestResultSerializer(serializers.ModelSerializer):
    test = TestSerializer()
    answers = StudentAnswerSerializer(many=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = StudentTest
        fields = [
            "uuid",
            "test",
            "status",
            "start_time",
            "end_time",
            "score",
            "answers",
            "duration",
        ]

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_duration(self, obj):
        """Get test duration in minutes"""
        return obj.duration


class TestAnswerSerializer(serializers.Serializer):
    """Serializer for submitting a single answer"""

    question = serializers.UUIDField()
    answer_text = serializers.CharField()
