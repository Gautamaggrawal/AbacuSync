from django.contrib import admin

from .models import Level, Student, StudentLevelHistory


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "name",
        "get_phone_number",
        "get_email",
        "gender",
        "centre",
        "ci",
        "current_level",
        "is_active",
    )
    list_filter = ("is_active", "gender", "centre", "current_level", "level_start_date")
    search_fields = (
        "name",
        "user__phone_number",
        "user__email",
        "centre__centre_name",
        "ci__name",
    )
    raw_id_fields = ("user", "centre", "ci", "current_level")
    date_hierarchy = "level_start_date"

    def get_phone_number(self, obj):
        return obj.user.phone_number

    get_phone_number.short_description = "Phone Number"
    get_phone_number.admin_order_field = "user__phone_number"

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"


@admin.register(StudentLevelHistory)
class StudentLevelHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "previous_level",
        "new_level",
        "start_date",
        "completion_date",
        "changed_by",
    )
    list_filter = ("start_date", "completion_date", "previous_level", "new_level")
    search_fields = (
        "student__name",
        "student__user__phone_number",
        "previous_level__name",
        "new_level__name",
    )
    raw_id_fields = ("student", "previous_level", "new_level", "changed_by")
    date_hierarchy = "start_date"


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "name", "description")
    search_fields = ("name", "description")
