# 用户账号管理系统 (User Account Management System)

一个功能完整的用户账号管理系统，使用 Flask 框架实现，提供用户注册、登录、配置文件管理和管理员功能。

## 功能特性 (Features)

### 用户功能
- ✅ 用户注册（带密码强度验证）
- ✅ 用户登录（JWT token 认证）
- ✅ 查看个人资料
- ✅ 更新个人资料（邮箱、全名）
- ✅ 修改密码
- ✅ 邮箱验证

### 管理员功能
- ✅ 查看所有用户列表
- ✅ 查看用户详细信息
- ✅ 更新用户角色（user/admin）
- ✅ 启用/禁用用户账户
- ✅ 删除用户

### 安全特性
- 🔒 密码加密存储（Bcrypt）
- 🔒 JWT token 认证
- 🔒 密码强度验证（至少8位，包含大小写字母和数字）
- 🔒 用户名和邮箱唯一性验证
- 🔒 输入数据验证和清理

## 技术栈 (Tech Stack)

- **后端框架**: Flask 2.3.3
- **数据库**: SQLAlchemy with SQLite (可替换为 PostgreSQL/MySQL)
- **认证**: Flask-JWT-Extended
- **密码加密**: Flask-Bcrypt
- **API跨域**: Flask-CORS
- **测试**: Pytest

## 快速开始 (Quick Start)

### 1. 环境要求
- Python 3.8+
- pip

### 2. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/wangyongzhao520/AI.git
cd AI

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者 Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置密钥
# SECRET_KEY=your-secret-key-here
# JWT_SECRET_KEY=your-jwt-secret-key-here
```

### 4. 运行应用

```bash
python run.py
```

服务器将在 `http://localhost:5000` 启动

### 5. 测试

```bash
# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=app tests/
```

## API 文档 (API Documentation)

### 基础端点

#### 健康检查
```
GET /api/health
```

响应示例:
```json
{
  "status": "healthy",
  "message": "User Account Management System is running"
}
```

### 认证端点

#### 用户注册
```
POST /api/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

响应示例 (201):
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2026-02-06T10:00:00",
    "updated_at": "2026-02-06T10:00:00",
    "last_login": null
  }
}
```

#### 用户登录
```
POST /api/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123"
}
```

响应示例 (200):
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    ...
  }
}
```

### 用户配置文件端点（需要认证）

所有以下端点需要在请求头中包含 JWT token:
```
Authorization: Bearer <access_token>
```

#### 获取当前用户资料
```
GET /api/profile
```

#### 更新当前用户资料
```
PUT /api/profile
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "John Updated Doe"
}
```

#### 修改密码
```
POST /api/change-password
Content-Type: application/json

{
  "old_password": "SecurePass123",
  "new_password": "NewSecurePass123"
}
```

### 管理员端点（需要管理员权限）

#### 获取所有用户列表
```
GET /api/users
```

响应示例:
```json
{
  "users": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      ...
    }
  ],
  "count": 1
}
```

#### 获取指定用户信息
```
GET /api/users/<user_id>
```

#### 更新用户（管理员）
```
PUT /api/users/<user_id>
Content-Type: application/json

{
  "role": "admin",
  "is_active": true
}
```

#### 删除用户
```
DELETE /api/users/<user_id>
```

## 数据库模型 (Database Schema)

### User 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(80) | 用户名（唯一） |
| email | String(120) | 邮箱（唯一） |
| password_hash | String(255) | 密码哈希 |
| full_name | String(100) | 全名 |
| role | String(20) | 角色 (user/admin) |
| is_active | Boolean | 账户状态 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| last_login | DateTime | 最后登录时间 |

## 项目结构 (Project Structure)

```
AI/
├── app/
│   ├── __init__.py       # Flask 应用初始化
│   ├── models.py         # 数据库模型
│   └── routes.py         # API 路由
├── tests/
│   ├── __init__.py
│   └── test_routes.py    # API 测试
├── .env.example          # 环境变量示例
├── .gitignore           # Git 忽略文件
├── requirements.txt      # Python 依赖
├── run.py               # 应用入口
└── README.md            # 项目文档
```

## 安全建议 (Security Recommendations)

1. **生产环境**: 
   - 使用强随机密钥设置 `SECRET_KEY` 和 `JWT_SECRET_KEY`
   - 使用 PostgreSQL 或 MySQL 替代 SQLite
   - 启用 HTTPS
   - 设置适当的 CORS 策略
   - **禁用 debug 模式**: 设置 `FLASK_DEBUG=false` 或不设置该环境变量

2. **密码策略**:
   - 至少 8 个字符
   - 包含大写字母、小写字母和数字
   - 可根据需要增强（特殊字符等）

3. **Token 管理**:
   - JWT token 默认无过期时间，建议在生产环境中设置过期时间
   - 考虑实现 refresh token 机制

4. **开发与生产**:
   - 开发环境: 设置 `FLASK_DEBUG=true` 启用调试模式
   - 生产环境: 务必设置 `FLASK_DEBUG=false` 或不设置该变量，使用生产级 WSGI 服务器（如 Gunicorn）

## 扩展功能建议 (Future Enhancements)

- [ ] 邮箱验证功能
- [ ] 密码重置（忘记密码）
- [ ] 双因素认证 (2FA)
- [ ] 用户头像上传
- [ ] 登录历史记录
- [ ] API 速率限制
- [ ] 日志记录和监控
- [ ] Swagger API 文档

## 贡献 (Contributing)

欢迎提交 Issue 和 Pull Request！

## 许可证 (License)

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式 (Contact)

如有问题或建议，请通过 GitHub Issues 联系。