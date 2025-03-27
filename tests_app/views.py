from django.db import transaction
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
from tests_app.models import (
    Question,
    StudentAnswer,
    StudentTest,
    Test,
    TestSession,
)

from .serializers import (
    ExcelUploadSerializer,
    StudentTestSerializer,
    TestAnswerSerializer,
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
    list=extend_schema(
        description="List all available tests for the student", tags=["Tests"]
    ),
    retrieve=extend_schema(
        description="Get details of a specific test", tags=["Tests"]
    ),
)
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"  # Add this line

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
            return Test.objects.filter(
                level=student.current_level, is_active=True
            )

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

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    create=extend_schema(description="Start a new test", tags=["Tests"]),
    retrieve=extend_schema(
        description="Get current test status and questions", tags=["Tests"]
    ),
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
    lookup_field = "uuid"

    def get_queryset(self):
        """Get student's tests"""
        student = get_object_or_404(Student, user=self.request.user)
        return StudentTest.objects.filter(student=student)

    def list(self, request, *args, **kwargs):
        """Get all test categories in a single response"""
        student = get_object_or_404(Student, user=request.user)

        # Get all available tests for student's level
        available_tests = Test.objects.filter(
            level=student.current_level, is_active=True
        )

        # Get student's taken tests
        taken_tests = StudentTest.objects.filter(student=student)

        # Past (completed) tests
        past_tests = taken_tests.filter(status="COMPLETED")

        # In-progress tests
        in_progress_tests = taken_tests.filter(
            status__in=["IN_PROGRESS", "INTERRUPTED", "PENDING"]
        )

        # Upcoming tests (not taken yet)
        taken_test_ids = taken_tests.values_list("test_id", flat=True)
        upcoming_tests = available_tests.exclude(id__in=taken_test_ids)

        # Serialize each category
        past_serializer = self.get_serializer(past_tests, many=True)
        in_progress_serializer = self.get_serializer(
            in_progress_tests, many=True
        )
        upcoming_serializer = TestSerializer(
            upcoming_tests, many=True
        )  # Use TestSerializer for upcoming tests

        return Response(
            {
                "past_tests": {
                    "count": past_tests.count(),
                    "results": past_serializer.data,
                },
                "in_progress_tests": {
                    "count": in_progress_tests.count(),
                    "results": in_progress_serializer.data,
                },
                "upcoming_tests": {
                    "count": upcoming_tests.count(),
                    "results": upcoming_serializer.data,
                },
            }
        )

    def create(self, request, *args, **kwargs):
        """Start a new test"""
        test_uuid = kwargs.get("test_uuid") or request.data.get("test_uuid")
        test = get_object_or_404(Test, uuid=test_uuid)
        student = get_object_or_404(Student, user=request.user)

        # Check if student already has an active test
        if StudentTest.objects.filter(student=student, test=test).exists():
            return Response(
                {"error": "You already have an active test"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create student test and session
        with transaction.atomic():
            student_test = StudentTest.objects.create(
                student=student, test=test, status="PENDING"
            )
            TestSession.objects.create(
                student_test=student_test,
                remaining_time_seconds=test.duration_minutes * 60,
            )

        serializer = self.get_serializer(student_test)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _update_remaining_time(self, student_test):
        """Helper method to update remaining time"""
        session = student_test.session
        if session and student_test.start_time:
            elapsed_time = (
                timezone.now() - student_test.start_time
            ).total_seconds()
            session.remaining_time_seconds = max(
                0, (student_test.test.duration_minutes * 60) - int(elapsed_time)
            )
            session.save()
        return session.remaining_time_seconds if session else 0

    @action(detail=True, methods=["get"])
    def remaining_duration(self, request, *args, **kwargs):
        """Get remaining duration for a test"""
        student_test = self.get_object()

        # If test is not in progress or interrupted, return 0
        if student_test.status not in ["IN_PROGRESS", "INTERRUPTED"]:
            return Response(
                {"remaining_duration": 0, "status": student_test.status}
            )

        # Get test session
        session = student_test.session
        if not session:
            return Response(
                {
                    "error": "No active session found",
                    "status": student_test.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate remaining time
        if student_test.status == "IN_PROGRESS":
            elapsed_time = (
                timezone.now() - student_test.start_time
            ).total_seconds()
            remaining_seconds = max(
                0, (student_test.test.duration_minutes * 60) - int(elapsed_time)
            )
        else:  # INTERRUPTED
            remaining_seconds = max(0, session.remaining_time_seconds)

        return Response(
            {
                "remaining_duration": remaining_seconds,
                "status": student_test.status,
                "total_duration": student_test.test.duration_minutes * 60,
                "start_time": student_test.start_time,
                "last_activity": session.last_sync,
            }
        )

    @action(detail=True, methods=["post"])
    def start(self, request, *args, **kwargs):
        """Start the test"""
        student_test = self.get_object()

        if student_test.status != "PENDING":
            return Response(
                {"error": "Test cannot be started"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_test.status = "IN_PROGRESS"
        student_test.start_time = timezone.now()
        student_test.save()

        # Reset session time when starting
        session = student_test.session
        if session:
            session.remaining_time_seconds = (
                student_test.test.duration_minutes * 60
            )
            session.last_sync = timezone.now()
            session.save()

        serializer = self.get_serializer(student_test)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def pause(self, request, *args, **kwargs):
        """Pause the test and save remaining time"""
        student_test = self.get_object()

        if student_test.status != "IN_PROGRESS":
            return Response(
                {"error": "Test is not in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        remaining_time = self._update_remaining_time(student_test)
        student_test.status = "INTERRUPTED"
        student_test.save()

        return Response(
            {"status": "Test paused", "remaining_time": remaining_time}
        )

    @action(detail=True, methods=["post"])
    def resume(self, request, *args, **kwargs):
        """Resume an interrupted test"""
        student_test = self.get_object()

        if student_test.status != "INTERRUPTED":
            return Response(
                {"error": "Test is not in interrupted state"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if test time has expired
        session = student_test.session
        if session and session.remaining_time_seconds <= 0:
            student_test.status = "COMPLETED"
            student_test.end_time = timezone.now()
            student_test.save()
            return Response(
                {"error": "Test time has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_test.status = "IN_PROGRESS"
        student_test.start_time = timezone.now()
        student_test.save()

        if session:
            session.last_sync = timezone.now()
            session.save()

        serializer = self.get_serializer(student_test)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit_answer(self, request, *args, **kwargs):
        """Submit a single answer during the test"""
        student_test = self.get_object()

        # Validate test status
        if student_test.status not in ["IN_PROGRESS"]:
            return Response(
                {"error": "Test is not in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check remaining time
        remaining_time = self._update_remaining_time(student_test)
        if remaining_time <= 0:
            student_test.status = "COMPLETED"
            student_test.end_time = timezone.now()
            student_test.save()
            return Response(
                {"error": "Test time has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate answer data
        serializer = TestAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # Save the answer
        question = get_object_or_404(
            Question, uuid=serializer.validated_data["question"]
        )
        StudentAnswer.objects.create(
            student_test=student_test,
            question=question,
            answer_text=serializer.validated_data["answer_text"],
        )

        return Response(
            {
                "status": "Answer submitted successfully",
                "remaining_time": remaining_time,
            }
        )

    @action(detail=True, methods=["post"])
    def end_test(self, request, *args, **kwargs):
        """End the test and mark it as completed"""
        student_test = self.get_object()

        # Validate test status
        if student_test.status not in ["IN_PROGRESS", "INTERRUPTED"]:
            return Response(
                {"error": "Test is not in progress or interrupted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark test as completed
        with transaction.atomic():
            student_test.status = "COMPLETED"
            student_test.end_time = timezone.now()
            student_test.save()

            # Calculate final score if needed
            # ... score calculation logic ...

        # Return test results
        result_serializer = TestResultSerializer(student_test)
        return Response(result_serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Get test status with remaining time"""
        student_test = self.get_object()
        if student_test.status in ["IN_PROGRESS"]:
            self._update_remaining_time(student_test)

        serializer = self.get_serializer(student_test)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def result(self, request, *args, **kwargs):
        """Get test result"""
        student_test = self.get_object()

        if student_test.status != "COMPLETED":
            return Response(
                {"error": "Test is not completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TestResultSerializer(student_test)
        return Response(serializer.data)
