# 快速开始指南 (Quick Start Guide)

本文档提供快速开始使用用户账号管理系统的步骤。

## 系统要求

- Python 3.8 或更高版本
- pip 包管理器

## 5分钟快速开始

### 1. 安装依赖 (1分钟)

```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 2. 配置环境 (1分钟)

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件（可选，开发环境可使用默认值）
# 生产环境务必修改 SECRET_KEY 和 JWT_SECRET_KEY
```

### 3. 启动服务器 (1分钟)

```bash
# 启动 Flask 开发服务器
python run.py
```

服务器将在 http://localhost:5000 启动

### 4. 测试 API (2分钟)

打开新终端，运行示例脚本：

```bash
python example_usage.py
```

或者使用 curl 命令：

```bash
# 健康检查
curl http://localhost:5000/api/health

# 注册用户
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "email": "demo@test.com",
    "password": "Demo1234",
    "full_name": "Demo User"
  }'

# 登录
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo",
    "password": "Demo1234"
  }'
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并显示详细输出
pytest -v

# 运行测试并显示覆盖率
pytest --cov=app tests/
```

## 主要 API 端点

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/api/health` | GET | 健康检查 | 否 |
| `/api/register` | POST | 用户注册 | 否 |
| `/api/login` | POST | 用户登录 | 否 |
| `/api/profile` | GET | 获取当前用户资料 | 是 |
| `/api/profile` | PUT | 更新当前用户资料 | 是 |
| `/api/change-password` | POST | 修改密码 | 是 |
| `/api/users` | GET | 获取所有用户（管理员） | 是 |
| `/api/users/<id>` | GET | 获取指定用户 | 是 |
| `/api/users/<id>` | PUT | 更新用户（管理员） | 是 |
| `/api/users/<id>` | DELETE | 删除用户（管理员） | 是 |

## 认证方式

所有需要认证的端点都需要在请求头中包含 JWT token：

```
Authorization: Bearer <your_jwt_token>
```

获取 token 的步骤：
1. 使用 `/api/login` 端点登录
2. 从响应中获取 `access_token`
3. 在后续请求的 Header 中添加 `Authorization: Bearer <access_token>`

## 密码要求

- 至少 8 个字符
- 必须包含至少一个大写字母
- 必须包含至少一个小写字母
- 必须包含至少一个数字

## 用户名要求

- 3-80 个字符
- 只能包含字母、数字和下划线

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 [API_DOCS.md](API_DOCS.md) 了解详细的 API 文档
- 运行 `example_usage.py` 查看完整的使用示例

## 常见问题

### Q: 如何创建管理员用户？

A: 首先注册一个普通用户，然后在数据库中手动将该用户的 `role` 字段设置为 `admin`。

```bash
# 使用 SQLite 命令行工具
sqlite3 user_accounts.db
sqlite> UPDATE users SET role='admin' WHERE username='your_username';
sqlite> .quit
```

### Q: 如何重置数据库？

A: 删除数据库文件后重启应用即可：

```bash
rm instance/user_accounts.db
python run.py
```

### Q: 生产环境如何部署？

A: 生产环境建议：
1. 使用生产级数据库（PostgreSQL/MySQL）
2. 设置强密钥（SECRET_KEY 和 JWT_SECRET_KEY）
3. 禁用调试模式（FLASK_DEBUG=false）
4. 使用生产级 WSGI 服务器（如 Gunicorn）
5. 配置反向代理（如 Nginx）
6. 启用 HTTPS

示例 Gunicorn 启动命令：
```bash
gunicorn -w 4 -b 0.0.0.0:8000 'app:app'
```

## 技术支持

如有问题，请访问 GitHub 仓库提交 Issue。
