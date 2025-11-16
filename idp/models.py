from django.db import models
from django.utils import timezone
import secrets


class OIDCClient(models.Model):
    """OIDC 客户端模型"""
    client_id = models.CharField(max_length=255, unique=True, db_index=True)
    client_secret = models.CharField(max_length=255)
    redirect_uri = models.URLField()
    name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'oidc_clients'
    
    def __str__(self):
        return f"{self.name or self.client_id}"


class AuthorizationCode(models.Model):
    """授权码模型"""
    code = models.CharField(max_length=255, unique=True, db_index=True)
    client = models.ForeignKey(OIDCClient, on_delete=models.CASCADE)
    redirect_uri = models.URLField()
    scope = models.CharField(max_length=500, default='openid')
    state = models.CharField(max_length=500, blank=True, null=True)
    nonce = models.CharField(max_length=500, blank=True, null=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'authorization_codes'
        indexes = [
            models.Index(fields=['code', 'is_used']),
        ]
    
    def __str__(self):
        return f"Code {self.code[:10]}... for {self.client.client_id}"
    
    def is_valid(self):
        """检查授权码是否有效"""
        return not self.is_used and self.expires_at > timezone.now()
    
    @classmethod
    def generate_code(cls):
        """生成授权码"""
        return secrets.token_urlsafe(32)


class AccessToken(models.Model):
    """访问令牌模型"""
    token = models.CharField(max_length=500, unique=True, db_index=True)
    client = models.ForeignKey(OIDCClient, on_delete=models.CASCADE)
    scope = models.CharField(max_length=500, default='openid')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'access_tokens'
    
    def __str__(self):
        return f"Token {self.token[:10]}... for {self.client.client_id}"
    
    def is_valid(self):
        """检查令牌是否有效"""
        return self.expires_at > timezone.now()
    
    @classmethod
    def generate_token(cls):
        """生成访问令牌"""
        return secrets.token_urlsafe(48)
