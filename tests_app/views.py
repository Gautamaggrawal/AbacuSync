from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from students.models import Student
from tests_app.models import Question, StudentAnswer, StudentTest, Test, TestSession

from .serializers import (
    ExcelUploadSerializer,
    StudentTestSerializer,
    TestResultSerializer,
    TestSerializer,
    TestSubmissionSerializer,
)


class ExcelUploadView(APIView):
    """View for handling Excel file uploads"""

    def post(self, request):
        """Handle POST request for file upload"""
        serializer = ExcelUploadSerializer(data=request.data)

        if serializer.is_valid():
            test = serializer.save()
            return Response(
                {
                    "message": "Test created successfully",
                    "test_id": str(test.id),
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(description="List all available tests for the student", tags=["Tests"]),
    retrieve=extend_schema(description="Get details of a specific test", tags=["Tests"]),
)
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"

    def get_queryset(self):
        """
        Get tests based on user type:
        - Admin/Center Staff: All tests
        - Student: Tests matching their current level
        """
        user = self.request.user

        # Check user type
        if user.user_type in ["ADMIN", "CENTRE"]:
            # Admin and center staff can see all active tests
            return Test.objects.filter(is_active=True)

        elif user.user_type == "STUDENT":
            # Students see only tests for their current level
            student = get_object_or_404(Student, user=user)
            return Test.objects.filter(level=student.current_level, is_active=True)

        # Default to empty queryset for any other user type
        return Test.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Optional: Add custom logic for list view if needed
        For example, adding extra context or filtering
        """
        level = self.request.query_params.get("level")

        queryset = self.filter_queryset(self.get_queryset())

        if level:
            queryset = queryset.filter(level__uuid=level)

        # Optional: Add extra filtering or context
        if request.user.user_type == "STUDENT":
            # Example of additional context for students
            student = get_object_or_404(Student, user=request.user)
            queryset = queryset.annotate(
                is_recommended=models.Case(
                    models.When(recommended_levels__contains=[student.current_level], then=True),
                    default=False,
                    output_field=models.BooleanField(),
                )
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    create=extend_schema(description="Start a new test", tags=["Tests"]),
    retrieve=extend_schema(description="Get current test status and questions", tags=["Tests"]),
    submit=extend_schema(
        description="Submit answers for the current test",
        request=TestSubmissionSerializer,
        responses={200: TestResultSerializer, 400: OpenApiTypes.OBJECT},
        tags=["Tests"],
    ),
)
class StudentTestViewSet(viewsets.ModelViewSet):
    serializer_class = StudentTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get student's tests"""
        student = get_object_or_404(Student, user=self.request.user)
        return StudentTest.objects.filter(student=student)

    def create(self, request, *args, **kwargs):
        """Start a new test"""
        test = get_object_or_404(Test, uuid=kwargs.get("test_uuid"))
        student = get_object_or_404(Student, user=request.user)

        # Check if student already has an active test
        if StudentTest.objects.filter(
            student=student, status__in=["PENDING", "IN_PROGRESS"]
        ).exists():
            return Response(
                {"error": "You already have an active test"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create student test and session
        with transaction.atomic():
            student_test = StudentTest.objects.create(student=student, test=test, status="PENDING")
            TestSession.objects.create(
                student_test=student_test, remaining_time_seconds=test.duration_minutes * 60
            )

        serializer = self.get_serializer(student_test)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def start(self, request, *args, **kwargs):
        """Start the test"""
        student_test = self.get_object()

        if student_test.status != "PENDING":
            return Response({"error": "Test cannot be started"}, status=status.HTTP_400_BAD_REQUEST)

        student_test.status = "IN_PROGRESS"
        student_test.start_time = timezone.now()
        student_test.save()

        serializer = self.get_serializer(student_test)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit(self, request, *args, **kwargs):
        """Submit test answers"""
        student_test = self.get_object()

        if student_test.status != "IN_PROGRESS":
            return Response(
                {"error": "Test is not in progress"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TestSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Process answers and calculate score
        with transaction.atomic():
            for answer_data in serializer.validated_data["answers"]:
                question = get_object_or_404(Question, uuid=answer_data["question"])
                StudentAnswer.objects.create(
                    student_test=student_test,
                    question=question,
                    answer_text=answer_data["answer_text"],
                )

            # Mark test as completed
            student_test.status = "COMPLETED"
            student_test.end_time = timezone.now()
            student_test.save()

        # Return test result
        result_serializer = TestResultSerializer(student_test)
        return Response(result_serializer.data)

    @action(detail=True, methods=["get"])
    def result(self, request, *args, **kwargs):
        """Get test result"""
        student_test = self.get_object()

        if student_test.status != "COMPLETED":
            return Response({"error": "Test is not completed"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TestResultSerializer(student_test)
        return Response(serializer.data)
