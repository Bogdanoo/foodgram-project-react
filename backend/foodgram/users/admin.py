from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "first_name", "last_name")
    ordering = ("id",)
    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
    )
    list_filter = (
        "email",
        "username",
    )
