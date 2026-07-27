from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('first_name', 'last_name', 'email', 'role', 'phone', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    readonly_fields = ('id','created_at', 'updated_at',)
    
    fieldsets = (

        ('Identification', {
            'fields': ('id', 'created_at', 'updated_at',)
        }),

        (None, {
            'fields': ('email', 'password', 'first_name', 'last_name', 'role', 'phone', 'photo')
        }),

        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'role', 'phone', 'photo'),
        }),
    )