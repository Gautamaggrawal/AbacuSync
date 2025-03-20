from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from centres.models import CI, Centre
from students.models import Level, Student, StudentLevelHistory
from users.models import User


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=15, required=True, help_text="User's phone number"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="User's password",
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")

        if phone_number and password:
            user = authenticate(
                request=self.context.get("request"),
                phone_number=phone_number,
                password=password,
            )

            if not user:
                msg = "Unable to log in with provided credentials."
                raise serializers.ValidationError(msg, code="authorization")

            if not user.is_active:
                msg = "User account is disabled."
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = 'Must include "phone_number" and "password".'
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class CISerializer(serializers.ModelSerializer):
    class Meta:
        model = CI
        fields = [
            "uuid",
            "name",
        ]


class CentreUserSerializer(serializers.ModelSerializer):
    generated_password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["uuid", "phone_number", "email", "is_active", "generated_password"]
        read_only_fields = ["uuid", "generated_password"]


class CentreSerializer(serializers.ModelSerializer):
    user = CentreUserSerializer()
    cis = CISerializer(many=True, required=False)
    student_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Centre
        fields = [
            "uuid",
            "user",
            "centre_name",
            "area",
            "is_active",
            "cis",
            "student_count",
            "created_at",
        ]
        read_only_fields = ["uuid"]

    def get_student_count(self, obj):
        return obj.students.count()

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        cis_data = validated_data.pop("cis", [])

        # Create user with centre type
        user_data["user_type"] = "CENTRE"
        generated_password = get_random_string(length=12)
        user_data["password"] = generated_password
        user = User.objects.create_user(**user_data)

        # Store generated password to return in response
        user.generated_password = generated_password

        # Create centre
        centre = Centre.objects.create(user=user, **validated_data)

        # Create CIs
        for ci_data in cis_data:
            CI.objects.create(centre=centre, **ci_data)

        return centre

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        cis_data = validated_data.pop("cis", [])

        # Update user
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Update centre
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update CIs
        if cis_data:
            instance.cis.all().delete()  # Remove existing CIs
            for ci_data in cis_data:
                CI.objects.get_or_create(centre=instance, **ci_data)

        return instance


class StudentUserSerializer(serializers.ModelSerializer):
    generated_password = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["uuid", "phone_number", "email", "is_active", "generated_password"]
        read_only_fields = ["uuid", "generated_password"]


class StudentSerializer(serializers.ModelSerializer):
    user = StudentUserSerializer()
    current_level = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Level.objects.all(),
    )
    ci = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=CI.objects.all(),
    )
    level_name = serializers.CharField(source="current_level.name", read_only=True)
    tests_taken = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "uuid",
            "ci",
            "user",
            "name",
            "dob",
            "gender",
            "current_level",
            "level_start_date",
            "level_completion_date",
            "is_active",
            "level_name",
            "tests_taken",
        ]
        read_only_fields = ["uuid"]

    @extend_schema_field(OpenApiTypes.INT)
    def get_tests_taken(self, obj) -> int:
        """Get number of completed tests for the student"""
        return obj.tests.filter(status="COMPLETED").count()

    def create(self, validated_data):
        user_data = validated_data.pop("user")

        # Create user with student type
        user_data["user_type"] = "STUDENT"
        generated_password = get_random_string(length=12)
        user_data["password"] = generated_password
        user_data["is_active"] = False  # Student needs admin approval
        user = User.objects.create_user(**user_data)

        # Store generated password to return in response
        user.generated_password = generated_password
        print(generated_password,"generated_password")

        # Create student
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        # Update user
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Update student
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class StudentLevelHistorySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    previous_level_name = serializers.CharField(source="previous_level.name", read_only=True)
    new_level_name = serializers.CharField(source="new_level.name", read_only=True)
    changed_by_name = serializers.CharField(source="changed_by.get_full_name", read_only=True)
    new_level = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Level.objects.all(),
    )
    student = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Student.objects.all(),
    )

    class Meta:
        model = StudentLevelHistory
        fields = [
            "uuid",
            "student",
            "previous_level",
            "new_level",
            "changed_by",
            "start_date",
            "completion_date",
            "created_at",
            "student_name",
            "previous_level_name",
            "new_level_name",
            "changed_by_name",
        ]
        read_only_fields = ["uuid", "created_at"]


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["uuid", "name", "description"]
        read_only_fields = ["uuid"]
