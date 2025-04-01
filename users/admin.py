from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token

from .models import Notification, User


class CustomTokenAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "_get_user_uuid",
        "user",
        "user__user_type",
        "created",
    )
    fields = ("user",)
    list_filter = ("user__user_type",)
    ordering = ("-created",)
    search_fields = ("user__username", "user__email", "key")

    def _get_user_uuid(self, obj):
        return obj.user.uuid


admin.site.register(Token, CustomTokenAdmin)

admin.site.register(Notification)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "phone_number",
        "email",
        "user_type",
        "is_active",
        "is_staff",
    )
    list_filter = ("user_type", "is_active", "is_staff")
    search_fields = ("phone_number", "email")
    ordering = ("phone_number",)

    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal info", {"fields": ("email", "user_type")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "email",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
