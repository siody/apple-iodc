from django.contrib import admin
from .models import OIDCClient, AuthorizationCode, AccessToken


@admin.register(OIDCClient)
class OIDCClientAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'name', 'redirect_uri', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['client_id', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuthorizationCode)
class AuthorizationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'client', 'redirect_uri', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['code', 'client__client_id']
    readonly_fields = ['code', 'created_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 编辑时
            return self.readonly_fields + ['client', 'redirect_uri', 'scope', 'state', 'nonce', 'expires_at']
        return self.readonly_fields


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'client', 'scope', 'expires_at', 'created_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['token', 'client__client_id']
    readonly_fields = ['token', 'created_at']
