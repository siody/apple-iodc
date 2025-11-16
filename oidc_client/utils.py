import json
import base64
import secrets
import requests
from urllib.parse import urlencode, parse_qs, urlparse
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from jose import jwt, jwk
from jose.utils import base64url_decode
import hashlib


def generate_state():
    """生成 state 参数用于 CSRF 保护"""
    return secrets.token_urlsafe(32)


def generate_nonce():
    """生成 nonce 参数用于重放攻击防护"""
    return secrets.token_urlsafe(32)


def get_apple_public_keys():
    """获取 Apple 的公钥用于验证 JWT"""
    try:
        response = requests.get(settings.OIDC_CONFIG['JWKS_URI'], timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取 Apple 公钥失败: {e}")
        return None


def verify_apple_token(id_token):
    """验证 Apple 返回的 ID token"""
    try:
        # 获取 Apple 公钥
        keys = get_apple_public_keys()
        if not keys:
            return None
        
        # 解析 token header
        unverified_header = jwt.get_unverified_header(id_token)
        
        # 找到匹配的密钥
        rsa_key = {}
        for key in keys['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
                break
        
        if not rsa_key:
            print("未找到匹配的密钥")
            return None
        
        # 验证并解码 token
        public_key = jwk.construct(rsa_key)
        decoded_token = jwt.decode(
            id_token,
            public_key,
            algorithms=['RS256'],
            audience=settings.OIDC_CONFIG['CLIENT_ID'],
            issuer='https://appleid.apple.com'
        )
        
        return decoded_token
    except Exception as e:
        print(f"验证 token 失败: {e}")
        return None


def get_authorization_url(request):
    """生成 Apple OIDC 授权 URL"""
    config = settings.OIDC_CONFIG
    
    # 生成 state 和 nonce
    state = generate_state()
    nonce = generate_nonce()
    
    # 存储到 session
    request.session['oidc_state'] = state
    request.session['oidc_nonce'] = nonce
    
    # 构建授权参数
    params = {
        'client_id': config['CLIENT_ID'],
        'redirect_uri': config['REDIRECT_URI'],
        'response_type': config['RESPONSE_TYPE'],
        'response_mode': config['RESPONSE_MODE'],
        'scope': config['SCOPE'],
        'state': state,
        'nonce': nonce,
    }
    
    # 构建授权 URL
    auth_url = f"{config['AUTHORIZATION_ENDPOINT']}?{urlencode(params)}"
    return auth_url


def exchange_code_for_tokens(code, request):
    """使用授权码交换访问令牌和 ID token"""
    config = settings.OIDC_CONFIG
    
    # 准备 token 请求
    token_data = {
        'client_id': config['CLIENT_ID'],
        'client_secret': config['CLIENT_SECRET'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': config['REDIRECT_URI'],
    }
    
    # 发送 token 请求
    try:
        response = requests.post(
            config['TOKEN_ENDPOINT'],
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"交换 token 失败: {e}")
        print(f"响应内容: {response.text if 'response' in locals() else '无响应'}")
        return None


def get_user_info(access_token):
    """使用访问令牌获取用户信息"""
    config = settings.OIDC_CONFIG
    
    try:
        response = requests.get(
            config['USERINFO_ENDPOINT'],
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None


