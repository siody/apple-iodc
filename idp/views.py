from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from .models import OIDCClient, AuthorizationCode, AccessToken


def get_base_url(request):
    """获取基础 URL"""
    scheme = request.scheme
    host = request.get_host()
    return f"{scheme}://{host}"


@require_http_methods(["GET"])
def authorization_endpoint(request):
    """
    授权端点
    根据 Apple 文档，直接返回授权码，不进行用户认证
    """
    # 获取 OIDC 标准参数
    client_id = request.GET.get('client_id')
    redirect_uri = request.GET.get('redirect_uri')
    response_type = request.GET.get('response_type', 'code')
    scope = request.GET.get('scope', 'openid')
    state = request.GET.get('state')
    nonce = request.GET.get('nonce')
    
    # 验证必需参数
    if not client_id or not redirect_uri:
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'client_id and redirect_uri are required'
        }, status=400)
    
    # 验证响应类型
    if response_type != 'code':
        return JsonResponse({
            'error': 'unsupported_response_type',
            'error_description': 'Only authorization code flow is supported'
        }, status=400)
    
    # 验证客户端
    try:
        client = OIDCClient.objects.get(client_id=client_id, is_active=True)
    except OIDCClient.DoesNotExist:
        return JsonResponse({
            'error': 'invalid_client',
            'error_description': 'Invalid client_id'
        }, status=400)
    
    # 验证重定向 URI
    if redirect_uri != client.redirect_uri:
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'redirect_uri mismatch'
        }, status=400)
    
    # 生成授权码（不进行用户认证，直接生成）
    code = AuthorizationCode.generate_code()
    authorization_code = AuthorizationCode.objects.create(
        code=code,
        client=client,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        nonce=nonce,
        expires_at=timezone.now() + timedelta(minutes=10)  # 授权码有效期 10 分钟
    )
    
    # 构建重定向 URL，添加授权码和状态
    parsed_uri = urlparse(redirect_uri)
    query_params = parse_qs(parsed_uri.query)
    query_params['code'] = [code]
    if state:
        query_params['state'] = [state]
    
    new_query = urlencode(query_params, doseq=True)
    redirect_url = urlunparse((
        parsed_uri.scheme,
        parsed_uri.netloc,
        parsed_uri.path,
        parsed_uri.params,
        new_query,
        parsed_uri.fragment
    ))
    
    # 重定向到 Apple 的回调地址
    return HttpResponseRedirect(redirect_url)


@require_http_methods(["POST"])
@csrf_exempt
def token_endpoint(request):
    """
    Token 端点
    使用授权码换取访问令牌
    """
    # 获取参数
    grant_type = request.POST.get('grant_type')
    code = request.POST.get('code')
    redirect_uri = request.POST.get('redirect_uri')
    client_id = request.POST.get('client_id')
    client_secret = request.POST.get('client_secret')
    
    # 验证必需参数
    if not grant_type or not code or not client_id or not client_secret:
        return JsonResponse({
            'error': 'invalid_request',
            'error_description': 'grant_type, code, client_id and client_secret are required'
        }, status=400)
    
    # 验证授权类型
    if grant_type != 'authorization_code':
        return JsonResponse({
            'error': 'unsupported_grant_type',
            'error_description': 'Only authorization_code grant type is supported'
        }, status=400)
    
    # 验证客户端
    try:
        client = OIDCClient.objects.get(client_id=client_id, is_active=True)
    except OIDCClient.DoesNotExist:
        return JsonResponse({
            'error': 'invalid_client',
            'error_description': 'Invalid client_id'
        }, status=400)
    
    # 验证客户端密钥
    if client_secret != client.client_secret:
        return JsonResponse({
            'error': 'invalid_client',
            'error_description': 'Invalid client_secret'
        }, status=400)
    
    # 验证授权码
    try:
        auth_code = AuthorizationCode.objects.get(code=code, client=client)
    except AuthorizationCode.DoesNotExist:
        return JsonResponse({
            'error': 'invalid_grant',
            'error_description': 'Invalid authorization code'
        }, status=400)
    
    # 检查授权码是否已使用或过期
    if auth_code.is_used:
        return JsonResponse({
            'error': 'invalid_grant',
            'error_description': 'Authorization code has already been used'
        }, status=400)
    
    if not auth_code.is_valid():
        return JsonResponse({
            'error': 'invalid_grant',
            'error_description': 'Authorization code has expired'
        }, status=400)
    
    # 验证重定向 URI
    if redirect_uri and redirect_uri != auth_code.redirect_uri:
        return JsonResponse({
            'error': 'invalid_grant',
            'error_description': 'redirect_uri mismatch'
        }, status=400)
    
    # 标记授权码为已使用
    auth_code.is_used = True
    auth_code.save()
    
    # 生成访问令牌
    access_token = AccessToken.generate_token()
    token_obj = AccessToken.objects.create(
        token=access_token,
        client=client,
        scope=auth_code.scope,
        expires_at=timezone.now() + timedelta(hours=1)  # Token 有效期 1 小时
    )
    
    # 构建响应
    response_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': auth_code.scope,
    }
    
    # 如果需要返回 ID Token（OIDC 标准），可以添加
    # 这里先简化，只返回 access_token
    
    return JsonResponse(response_data)


@require_http_methods(["GET"])
def discovery_endpoint(request):
    """
    OIDC 发现端点
    返回 OIDC 配置信息
    """
    base_url = get_base_url(request)
    
    discovery_config = {
        'issuer': base_url,
        'authorization_endpoint': f"{base_url}/oidc/authorize",
        'token_endpoint': f"{base_url}/oidc/token",
        'userinfo_endpoint': f"{base_url}/oidc/userinfo",
        'jwks_uri': f"{base_url}/oidc/jwks",
        'response_types_supported': ['code'],
        'subject_types_supported': ['public'],
        'id_token_signing_alg_values_supported': ['RS256'],
        'scopes_supported': ['openid', 'ssf.manage', 'ssf.read'],
        'token_endpoint_auth_methods_supported': ['client_secret_post'],
        'grant_types_supported': ['authorization_code', 'refresh_token'],
    }
    
    return JsonResponse(discovery_config)


@require_http_methods(["GET"])
def jwks_endpoint(request):
    """
    JWKS 端点
    返回公钥信息（用于验证 ID Token）
    """
    # 这里简化处理，实际应该返回真实的 JWK
    # 如果需要支持 ID Token，需要实现密钥管理
    jwks = {
        'keys': []
    }
    
    return JsonResponse(jwks)


@require_http_methods(["GET", "POST"])
@csrf_exempt
def userinfo_endpoint(request):
    """
    用户信息端点
    返回用户信息（需要 access_token）
    """
    # 从请求头或参数中获取 access_token
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        access_token = auth_header[7:]
    else:
        access_token = request.GET.get('access_token') or request.POST.get('access_token')
    
    if not access_token:
        return JsonResponse({
            'error': 'invalid_token',
            'error_description': 'Access token is required'
        }, status=401)
    
    # 验证访问令牌
    try:
        token_obj = AccessToken.objects.get(token=access_token)
    except AccessToken.DoesNotExist:
        return JsonResponse({
            'error': 'invalid_token',
            'error_description': 'Invalid access token'
        }, status=401)
    
    if not token_obj.is_valid():
        return JsonResponse({
            'error': 'invalid_token',
            'error_description': 'Access token has expired'
        }, status=401)
    
    # 返回用户信息（简化版本）
    user_info = {
        'sub': 'user@example.com',  # 主题标识符
        'email': 'user@example.com',
        'email_verified': True,
    }
    
    return JsonResponse(user_info)
