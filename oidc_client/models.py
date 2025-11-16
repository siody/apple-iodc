from django.db import models
from django.contrib.auth.models import User


class OIDCUser(models.Model):
    """存储 OIDC 用户信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='oidc_user')
    sub = models.CharField(max_length=255, unique=True, help_text="Apple 用户唯一标识")
    email = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'oidc_user'
        verbose_name = 'OIDC 用户'
        verbose_name_plural = 'OIDC 用户'
    
    def __str__(self):
        return f"{self.user.username} ({self.sub})"


