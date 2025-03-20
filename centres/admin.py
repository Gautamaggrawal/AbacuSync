from django.contrib import admin

from .models import CI, Centre


@admin.register(Centre)
class CentreAdmin(admin.ModelAdmin):
    list_display = ("uuid", "centre_name", "area", "get_phone_number", "get_email", "is_active")
    list_filter = ("is_active", "area")
    search_fields = ("centre_name", "area", "user__phone_number", "user__email")
    raw_id_fields = ("user",)

    def get_phone_number(self, obj):
        return obj.user.phone_number

    get_phone_number.short_description = "Phone Number"
    get_phone_number.admin_order_field = "user__phone_number"

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"
    get_email.admin_order_field = "user__email"


@admin.register(CI)
class CIAdmin(admin.ModelAdmin):
    list_display = ("uuid", "name", "centre", "get_centre_name")
    list_filter = ("centre",)
    search_fields = ("name", "centre__centre_name")
    raw_id_fields = ("centre",)

    def get_centre_name(self, obj):
        return obj.centre.centre_name

    get_centre_name.short_description = "Centre Name"
    get_centre_name.admin_order_field = "centre__centre_name"
