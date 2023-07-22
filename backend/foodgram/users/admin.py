from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe, User


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


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    search_fields = ('user', 'author',)
    list_filter = ('user', 'author',)
