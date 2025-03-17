from django.contrib import admin
from django.utils.translation import gettext_lazy as _
# Register your models here.
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    
    list_display = ("phone_number", "email", "user_type", "is_staff", "is_superuser")
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type')
    search_fields = ("phone_number", "email", "user_type", "uuid")
    ordering = ('phone_number',)
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('User type'), {'fields': ('user_type',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'email', 'user_type', 'password1', 'password2'),
        }),
    )
