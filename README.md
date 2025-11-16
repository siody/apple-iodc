# Apple Business Manager OIDC 集成

这是一个使用 Django 实现的 Apple Business Manager OIDC（OpenID Connect）集成项目。

## 功能特性

- ✅ 完整的 OIDC 认证流程
- ✅ Apple ID token 验证
- ✅ 用户信息获取和存储
- ✅ 自动用户创建
- ✅ Session 管理
- ✅ CSRF 和重放攻击防护

## 环境要求

- Python 3.8+
- Django 4.2+
- Apple Business Manager 账户和开发者权限

## 安装步骤

### 1. 克隆项目并安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env` 并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入以下信息：

- `SECRET_KEY`: Django 密钥（可使用 `python manage.py generatesecretkey` 生成）
- `OIDC_CLIENT_ID`: Apple Business Manager 应用客户端 ID
- `OIDC_CLIENT_SECRET`: Apple Business Manager 应用客户端密钥
- `OIDC_REDIRECT_URI`: 回调 URL（必须在 Apple 开发者后台注册）

### 3. 在 Apple Business Manager 中注册应用

1. 登录 [Apple Business Manager](https://business.apple.com)
2. 进入开发者设置
3. 创建新的 App ID 和服务 ID
4. 配置 OIDC 重定向 URI（必须与 `OIDC_REDIRECT_URI` 完全一致）
5. 获取 Client ID 和 Client Secret

参考文档：https://support.apple.com/en-au/guide/apple-business-manager/axmfcab66783/web

### 4. 初始化数据库

```bash
python manage.py migrate
python manage.py createsuperuser  # 可选，用于 Django Admin
```

### 5. 运行开发服务器

```bash
python manage.py runserver
```

访问 http://localhost:8000 查看应用。

## 使用说明

### 登录流程

1. 用户访问首页，点击"使用 Apple 登录"
2. 重定向到 Apple 授权页面
3. 用户输入 Apple ID 并授权
4. Apple 重定向回应用（使用 form_post 模式）
5. 应用验证 token 并创建/登录用户
6. 用户登录成功

### API 端点

- `/oidc/login/` - 发起 OIDC 登录
- `/oidc/callback/` - OIDC 回调处理
- `/oidc/logout/` - 用户登出
- `/admin/` - Django Admin 后台

### 用户模型

项目使用 Django 默认 User 模型，并扩展了 `OIDCUser` 模型存储 Apple 用户信息：

- `sub`: Apple 用户唯一标识
- `email`: 用户邮箱
- `email_verified`: 邮箱是否已验证

## 配置说明

### OIDC 配置

在 `settings.py` 中，所有 OIDC 配置都通过环境变量读取：

```python
OIDC_CONFIG = {
    'CLIENT_ID': env('OIDC_CLIENT_ID'),
    'CLIENT_SECRET': env('OIDC_CLIENT_SECRET'),
    'REDIRECT_URI': env('OIDC_REDIRECT_URI'),
    'SCOPE': env('OIDC_SCOPE', default='openid email profile'),
    # ...
}
```

### Apple 特定配置

- `response_mode`: 设置为 `form_post`（Apple 推荐）
- `response_type`: 设置为 `code`（授权码模式）
- Token 验证使用 Apple 的 JWKS 端点

## 安全注意事项

1. **生产环境配置**：
   - 设置 `DEBUG=False`
   - 使用强密钥 `SECRET_KEY`
   - 启用 HTTPS（`SESSION_COOKIE_SECURE=True`）
   - 配置正确的 `ALLOWED_HOSTS`

2. **Token 验证**：
   - ID token 使用 Apple 公钥验证
   - 验证 audience、issuer、nonce
   - 验证 state 防止 CSRF 攻击

3. **敏感信息**：
   - 不要在代码中硬编码密钥
   - 使用环境变量存储敏感配置
   - 不要提交 `.env` 文件到版本控制

## 故障排除

### 常见问题

1. **"OIDC 配置不完整"错误**
   - 检查 `.env` 文件是否正确配置
   - 确认环境变量已加载

2. **"State 验证失败"错误**
   - 检查 session 配置
   - 确认没有多个服务器实例共享 session

3. **"ID token 验证失败"错误**
   - 检查 CLIENT_ID 是否正确
   - 确认网络可以访问 Apple JWKS 端点
   - 检查系统时间是否准确

4. **回调 URL 不匹配**
   - 确保 Apple 开发者后台配置的 Redirect URI 与 `OIDC_REDIRECT_URI` 完全一致
   - 包括协议（http/https）、域名、端口、路径

## 开发

### 运行测试

```bash
python manage.py test
```

### 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

## 许可证

MIT License

## 参考资源

- [Apple Business Manager OIDC 文档](https://support.apple.com/en-au/guide/apple-business-manager/axmfcab66783/web)
- [Django 文档](https://docs.djangoproject.com/)
- [OpenID Connect 规范](https://openid.net/connect/)


