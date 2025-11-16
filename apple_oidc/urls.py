"""
URL configuration for apple_oidc project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('oidc_client.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]


