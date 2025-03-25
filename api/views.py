from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from centres.models import Centre
from students.models import Level, Student, StudentLevelHistory
from users.models import User

from .permissions import IsAdmin
from .serializers import (
    CentreSerializer,
    LevelSerializer,
    LoginSerializer,
    StudentLevelHistorySerializer,
    StudentSerializer,
)


@extend_schema(
    request=LoginSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "user_type": {"type": "string"},
                "user_data": {"type": "object"},
            },
        }
    },
    description="Login endpoint for all user types (Admin, Centre, Student)",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login endpoint for all user types.
    Returns authentication token and user details based on user type.
    """
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    token, created = Token.objects.get_or_create(user=user)

    # Log the user in
    login(request, user)

    # Prepare response based on user type
    response_data = {
        "token": token.key,
        "user_type": user.user_type,
    }

    # Add user-specific data based on user type
    if user.user_type == "ADMIN":
        response_data["user_data"] = {
            "uuid": str(user.uuid),
            "email": user.email,
            "phone_number": user.phone_number,
            "total_centers": Centre.objects.count(),
            "active_users": User.objects.filter(is_active=True, user_type="STUDENT").count(),
        }
    elif user.user_type == "CENTRE":
        centre = user.centre_profile
        response_data["user_data"] = CentreSerializer(centre).data
    elif user.user_type == "STUDENT":
        student = user.student_profile
        response_data["user_data"] = StudentSerializer(student).data

    return Response(response_data)


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Successfully logged out.")


@extend_schema(
    responses={200: LogoutResponseSerializer, 401: OpenApiTypes.OBJECT},
    description="Logout endpoint that invalidates the user's auth token",
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout endpoint.
    Deletes the user's auth token.
    """
    request.user.auth_token.delete()
    return Response({"message": "Successfully logged out."})


@extend_schema_view(
    list=extend_schema(
        description="List all centres/franchisees",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search in centre_name, franchisee_name, area, phone_number, email",
            )
        ],
    ),
    create=extend_schema(description="Create a new centre/franchisee"),
    retrieve=extend_schema(description="Get a specific centre/franchisee details"),
    update=extend_schema(description="Update a centre/franchisee"),
    partial_update=extend_schema(description="Partially update a centre/franchisee"),
    destroy=extend_schema(description="Delete a centre/franchisee"),
)
class CentreViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing centres/franchisees.
    Only admin can create, update, and delete centres.
    """

    serializer_class = CentreSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["centre_name", "area", "user__phone_number", "user__email"]
    lookup_field = "uuid"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Centre.objects.none()
        return Centre.objects.all().select_related("user").prefetch_related("cis")

    @extend_schema(
        description="Reset password for centre user",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["post"])
    def reset_password(self, request, uuid=None):
        """Reset password for centre user"""
        centre = self.get_object()
        new_password = get_random_string(length=12)

        try:
            validate_password(new_password, centre.user)
            centre.user.set_password(new_password)
            centre.user.save()
            return Response({"password": new_password})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Toggle active status of centre",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["post"])
    def toggle_active(self, request, uuid=None):
        """Toggle active status of centre"""
        centre = self.get_object()
        centre.is_active = not centre.is_active
        centre.user.is_active = centre.is_active
        centre.user.save()
        centre.save()
        return Response({"status": "success", "is_active": centre.is_active})

    @extend_schema(
        description="Get list of students for a centre",
        responses={200: StudentSerializer(many=True)},
    )
    @action(detail=True)
    def students(self, request, uuid=None):
        """Get list of students for a centre"""
        centre = self.get_object()
        students = centre.students.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        description="List all students",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search in name, phone_number, email",
            )
        ],
    ),
    create=extend_schema(description="Create a new student"),
    retrieve=extend_schema(description="Get a specific student's details"),
    update=extend_schema(description="Update a student"),
    partial_update=extend_schema(description="Partially update a student"),
    destroy=extend_schema(description="Delete a student"),
)
class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students.
    Centres can only manage their own students.
    Admin can manage all students.
    """

    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "user__phone_number", "user__email"]
    lookup_field = "uuid"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Student.objects.none()
        queryset = Student.objects.all().select_related("user", "centre", "current_level", "ci")
        if self.request.user.user_type == "CENTRE":
            return queryset.filter(centre__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        if self.request.user.user_type == "CENTRE":
            serializer.save(centre=self.request.user.centre_profile)
        else:
            serializer.save()

    @extend_schema(description="Reset password for student", responses={200: OpenApiTypes.OBJECT})
    @action(detail=True, methods=["post"])
    def reset_password(self, request, uuid=None):
        """Reset password for student"""
        student = self.get_object()
        new_password = get_random_string(length=12)

        try:
            validate_password(new_password, student.user)
            student.user.set_password(new_password)
            student.user.save()
            return Response({"password": new_password})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Toggle active status of student",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def toggle_active(self, request, uuid=None):
        """Toggle active status of student with atomic transaction"""
        try:
            # Retrieve the student object within the transaction
            student = self.get_object()
            was_inactive = not student.user.is_active  # Check if the user was inactive

            # Toggle the active status
            student.user.is_active = not student.user.is_active

            # If student is being activated
            current_date = timezone.now().date()
            if (
                student.user.is_active
                and was_inactive
                and not StudentLevelHistory.objects.filter(student=student).exist()
            ):
                # Create level history entry
                StudentLevelHistory.objects.create(
                    student=student,
                    new_level=student.current_level,
                    start_date=current_date,
                    completion_date=None,
                    changed_by=request.user,
                )

            # Save both user and student models
            student.user.save()
            student.save()

            return Response({"status": "success", "is_active": student.user.is_active})

        except Exception as e:
            # Rollback will be automatic due to @transaction.atomic
            return Response({"status": "error", "message": str(e)}, status=400)

    @extend_schema(description="Approve student (admin only)", responses={200: OpenApiTypes.OBJECT})
    @action(detail=True, methods=["post"])
    def approve(self, request, uuid=None):
        """Approve student (admin only)"""
        if not request.user.user_type == "ADMIN":
            return Response(
                {"error": "Only admin can approve students"},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = self.get_object()
        student.user.is_active = True
        student.user.save()
        return Response({"status": "success"})

    @extend_schema(
        description="Get level history for a student",
        responses={200: StudentLevelHistorySerializer(many=True)},
    )
    @action(detail=True)
    def level_history(self, request, uuid=None):
        """Get level history for a student"""
        student = self.get_object()
        history = student.level_history.all().select_related("new_level", "changed_by")
        serializer = StudentLevelHistorySerializer(history, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description="List all student level history entries"),
    create=extend_schema(description="Create a new level history entry"),
    retrieve=extend_schema(description="Get a specific level history entry"),
    update=extend_schema(description="Update a level history entry"),
    partial_update=extend_schema(description="Partially update a level history entry"),
    destroy=extend_schema(description="Delete a level history entry"),
)
class StudentLevelHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student level history.
    Read-only for centres (their own students only).
    Admin can view all.
    """

    serializer_class = StudentLevelHistorySerializer
    permission_classes = [IsAuthenticated]
    queryset = StudentLevelHistory.objects.none()  # For Swagger
    lookup_field = "uuid"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentLevelHistory.objects.none()
        queryset = StudentLevelHistory.objects.all().select_related(
            "student", "new_level", "changed_by"
        )
        if self.request.user.user_type == "CENTRE":
            return queryset.filter(student__centre__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """
        Efficiently create a new level history entry with atomic transaction
        - Updates previous level history completion date
        - Sets new student level
        - Ensures data consistency
        """
        with transaction.atomic():
            student = serializer.validated_data["student"]
            new_level = serializer.validated_data["new_level"]
            curr_date = timezone.now().date()

            # Efficiently update last uncompleted level history in a single query
            StudentLevelHistory.objects.filter(
                student=student, completion_date__isnull=True
            ).update(completion_date=curr_date)

            # Bulk update student attributes
            Student.objects.filter(pk=student.pk).update(
                current_level=new_level, level_start_date=curr_date
            )

            # Create new level history with the current user
            level_history = serializer.save(changed_by=self.request.user)
            return level_history


@extend_schema_view(
    list=extend_schema(description="List all levels"),
    retrieve=extend_schema(description="Get a specific level's details"),
)
class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing levels.
    Read-only for all authenticated users.
    """

    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
