import logging
from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.urls import reverse
from .utils import (
    get_authorization_url,
    exchange_code_for_tokens,
    verify_apple_token,
    get_user_info
)
from .models import OIDCUser

logger = logging.getLogger(__name__)


def oidc_login(request):
    """发起 OIDC 登录流程"""
    if not settings.OIDC_CONFIG['CLIENT_ID']:
        return HttpResponse(
            "OIDC 配置不完整，请设置 OIDC_CLIENT_ID 环境变量",
            status=500
        )
    
    # 生成授权 URL 并重定向
    auth_url = get_authorization_url(request)
    return redirect(auth_url)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def oidc_callback(request):
    """处理 OIDC 回调"""
    try:
        # Apple 使用 form_post 模式，从 POST 数据中获取
        if request.method == 'POST':
            code = request.POST.get('code')
            state = request.POST.get('state')
            error = request.POST.get('error')
            error_description = request.POST.get('error_description')
        else:
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            error_description = request.GET.get('error_description')
        
        # 检查错误
        if error:
            logger.error(f"OIDC 回调错误: {error} - {error_description}")
            return HttpResponse(
                f"认证失败: {error} - {error_description}",
                status=400
            )
        
        # 验证 state
        session_state = request.session.get('oidc_state')
        if not session_state or state != session_state:
            logger.error("State 验证失败")
            return HttpResponse("State 验证失败", status=400)
        
        # 验证 code
        if not code:
            logger.error("未收到授权码")
            return HttpResponse("未收到授权码", status=400)
        
        # 交换 token
        token_response = exchange_code_for_tokens(code, request)
        if not token_response:
            logger.error("交换 token 失败")
            return HttpResponse("交换 token 失败", status=500)
        
        id_token = token_response.get('id_token')
        access_token = token_response.get('access_token')
        
        if not id_token:
            logger.error("未收到 ID token")
            return HttpResponse("未收到 ID token", status=500)
        
        # 验证 ID token
        decoded_token = verify_apple_token(id_token)
        if not decoded_token:
            logger.error("ID token 验证失败")
            return HttpResponse("ID token 验证失败", status=500)
        
        # 验证 nonce
        session_nonce = request.session.get('oidc_nonce')
        token_nonce = decoded_token.get('nonce')
        if session_nonce and token_nonce != session_nonce:
            logger.error("Nonce 验证失败")
            return HttpResponse("Nonce 验证失败", status=400)
        
        # 获取用户信息
        sub = decoded_token.get('sub')
        email = decoded_token.get('email')
        email_verified = decoded_token.get('email_verified', False)
        
        # 如果 token 中没有 email，尝试使用 access_token 获取
        if not email and access_token:
            user_info = get_user_info(access_token)
            if user_info:
                email = user_info.get('email') or email
                email_verified = user_info.get('email_verified', email_verified)
        
        if not sub:
            logger.error("未找到用户标识")
            return HttpResponse("未找到用户标识", status=500)
        
        # 获取或创建用户
        oidc_user, created = OIDCUser.objects.get_or_create(
            sub=sub,
            defaults={
                'email': email,
                'email_verified': email_verified,
            }
        )
        
        # 如果用户已存在，更新信息
        if not created:
            oidc_user.email = email or oidc_user.email
            oidc_user.email_verified = email_verified
            oidc_user.save()
        
        # 如果 OIDCUser 没有关联的 Django User，创建一个
        if not oidc_user.user:
            # 生成用户名
            username = email.split('@')[0] if email else f"apple_user_{sub[:8]}"
            # 确保用户名唯一
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            
            # 创建 Django User
            user = User.objects.create_user(
                username=username,
                email=email or '',
                first_name=decoded_token.get('given_name', ''),
                last_name=decoded_token.get('family_name', ''),
            )
            oidc_user.user = user
            oidc_user.save()
        
        # 登录用户
        login(request, oidc_user.user, backend='django.contrib.auth.backends.ModelBackend')
        
        # 清除 session 中的 state 和 nonce
        request.session.pop('oidc_state', None)
        request.session.pop('oidc_nonce', None)
        
        # 重定向到首页
        return redirect(settings.LOGIN_REDIRECT_URL)
        
    except Exception as e:
        logger.exception(f"OIDC 回调处理异常: {e}")
        return HttpResponse(f"处理回调时发生错误: {str(e)}", status=500)


def oidc_logout(request):
    """登出用户"""
    logout(request)
    return redirect(settings.LOGIN_REDIRECT_URL)


