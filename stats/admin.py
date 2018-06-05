from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# from app1.forms import CustomUserChangeForm, CustomUserCreationForm

# Register your models here.
from .models import CustomUser
# from .models import User
# admin.site.register(User)

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'email', 'uri', 'access_token', 'refresh_token', 'token')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    list_display = ('username', 'email', 'name')
    search_fields = ('username', 'email', 'name')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
