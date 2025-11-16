"""
Django settings for apple_oidc project.
"""

import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file (fallback to 'env' file if .env doesn't exist)
env_file = os.path.join(BASE_DIR, '.env')
if not os.path.exists(env_file):
    env_file = os.path.join(BASE_DIR, 'env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
# Handle both string and boolean values for DEBUG
debug_value = env('DEBUG', default=False)
if isinstance(debug_value, str):
    DEBUG = debug_value.lower() in ('true', '1', 'yes', 'on')
else:
    DEBUG = bool(debug_value)

# ALLOWED_HOSTS can be a string (comma-separated) or list
allowed_hosts_str = env('ALLOWED_HOSTS', default='localhost,127.0.0.1')
if isinstance(allowed_hosts_str, str):
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = allowed_hosts_str or ['localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oidc_client',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'apple_oidc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'apple_oidc.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OIDC Configuration for Apple Business Manager
OIDC_CONFIG = {
    # Apple Business Manager OIDC 端点
    'AUTHORIZATION_ENDPOINT': env(
        'OIDC_AUTHORIZATION_ENDPOINT',
        default='https://appleid.apple.com/auth/authorize'
    ),
    'TOKEN_ENDPOINT': env(
        'OIDC_TOKEN_ENDPOINT',
        default='https://appleid.apple.com/auth/token'
    ),
    'USERINFO_ENDPOINT': env(
        'OIDC_USERINFO_ENDPOINT',
        default='https://appleid.apple.com/auth/userinfo'
    ),
    'JWKS_URI': env(
        'OIDC_JWKS_URI',
        default='https://appleid.apple.com/auth/keys'
    ),
    # 客户端配置
    'CLIENT_ID': env('OIDC_CLIENT_ID', default=''),
    'CLIENT_SECRET': env('OIDC_CLIENT_SECRET', default=''),
    'REDIRECT_URI': env('OIDC_REDIRECT_URI', default='http://localhost:8000/oidc/callback/'),
    'SCOPE': env('OIDC_SCOPE', default='openid email profile'),
    # Apple 特定配置
    'RESPONSE_TYPE': 'code',
    'RESPONSE_MODE': 'form_post',  # Apple 推荐使用 form_post
}

# 登录重定向 URL
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/oidc/login/'

# Session 配置
# 从环境变量读取，如果未设置则根据 DEBUG 自动判断
session_secure = env('SESSION_COOKIE_SECURE', default=None)
if session_secure is None:
    SESSION_COOKIE_SECURE = not DEBUG
elif isinstance(session_secure, str):
    SESSION_COOKIE_SECURE = session_secure.lower() in ('true', '1', 'yes', 'on')
else:
    SESSION_COOKIE_SECURE = bool(session_secure)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'


