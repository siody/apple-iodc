#!/usr/bin/env python
"""
创建 Apple Business Manager OIDC 客户端
使用方法: python create_apple_client.py
"""
import os
import sys
import django
import secrets

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apple_oidc.settings')
django.setup()

from idp.models import OIDCClient


def create_apple_client():
    """创建 Apple Business Manager 客户端"""
    
    # Apple 要求的重定向 URI
    redirect_uri = "https://gsa-ws.apple.com/grandslam/GsService2/acs"
    
    # 生成客户端 ID 和密钥
    client_id = f"AppleBusinessManagerOIDC_{secrets.token_urlsafe(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    # 检查是否已存在客户端
    if OIDCClient.objects.filter(redirect_uri=redirect_uri).exists():
        print("已存在 Apple Business Manager 客户端")
        client = OIDCClient.objects.get(redirect_uri=redirect_uri)
        print(f"Client ID: {client.client_id}")
        print(f"Client Secret: {client.client_secret}")
        return client
    
    # 创建新客户端
    client = OIDCClient.objects.create(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        name="Apple Business Manager OIDC",
        is_active=True
    )
    
    print("=" * 60)
    print("Apple Business Manager OIDC 客户端创建成功！")
    print("=" * 60)
    print(f"Client ID: {client.client_id}")
    print(f"Client Secret: {client.client_secret}")
    print(f"Redirect URI: {client.redirect_uri}")
    print("=" * 60)
    print("\n请在 Apple Business Manager 中配置以下信息：")
    print(f"- OIDC Client ID: {client.client_id}")
    print(f"- OIDC Client Secret: {client.client_secret}")
    print(f"- Authorization endpoint: <你的域名>/oidc/authorize")
    print(f"- Token endpoint: <你的域名>/oidc/token")
    print(f"- OIDC Discovery: <你的域名>/.well-known/openid-configuration")
    print("=" * 60)
    
    return client


if __name__ == '__main__':
    create_apple_client()

