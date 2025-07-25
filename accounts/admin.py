from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User
from .forms import UserCreationForm, UserChangeForm


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ["username",]
    list_filter = ["username",]
    fieldsets = (
        (None, {"fields": ("username", "password", )}),
        ("Permissions", {"fields": ("is_active", "level_access")}),
    )

    add_fieldsets = (
        (None, {"fields": ("username", "password", "password2", )}),
        ("Permissions", {"fields": ("is_active", "level_access")}),
    )

    search_fields = ["username", ]

    ordering = ["username"]
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
