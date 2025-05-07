from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

class ChangePasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(phone_number=data['phone_number']).first()
        if not user:
            raise serializers.ValidationError("User with this phone number does not exist.")
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError("Old password is incorrect.")
        validate_password(data['new_password'], user)
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(phone_number=data['phone_number']).first()
        if not user:
            raise serializers.ValidationError("User with this phone number does not exist.")
        validate_password(data['new_password'], user)
        return data 