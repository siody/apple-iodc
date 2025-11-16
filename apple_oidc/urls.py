"""
URL configuration for apple_oidc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from idp import views as idp_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # OIDC 端点
    path('oidc/authorize', idp_views.authorization_endpoint, name='oidc_authorize'),
    path('oidc/token', idp_views.token_endpoint, name='oidc_token'),
    path('oidc/userinfo', idp_views.userinfo_endpoint, name='oidc_userinfo'),
    path('oidc/jwks', idp_views.jwks_endpoint, name='oidc_jwks'),
    # OIDC 发现端点
    path('.well-known/openid-configuration', idp_views.discovery_endpoint, name='oidc_discovery'),
]
