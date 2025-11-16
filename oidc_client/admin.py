from django.contrib import admin
from .models import OIDCUser


@admin.register(OIDCUser)
class OIDCUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'sub', 'email', 'email_verified', 'created_at')
    list_filter = ('email_verified', 'created_at')
    search_fields = ('user__username', 'email', 'sub')
    readonly_fields = ('created_at', 'updated_at')


