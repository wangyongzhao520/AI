# API Documentation

## Overview
This is a RESTful API for user account management with JWT authentication.

## Base URL
```
http://localhost:5000/api
```

## Authentication
Most endpoints require JWT token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Public Endpoints

#### Health Check
Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "message": "User Account Management System is running"
}
```

#### Register User
Create a new user account.

**Endpoint:** `POST /register`

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Validation Rules:**
- Username: 3-80 characters, alphanumeric and underscores only
- Email: Valid email format
- Password: Minimum 8 characters, must contain uppercase, lowercase, and digit
- Full name: Optional

**Success Response:** `201 Created`
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

**Error Responses:**
- `400 Bad Request` - Validation failed or user already exists
- `500 Internal Server Error` - Server error

#### Login
Authenticate and receive JWT token.

**Endpoint:** `POST /login`

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "SecurePass123"
}
```

**Success Response:** `200 OK`
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2026-02-06T10:00:00",
    "updated_at": "2026-02-06T10:00:00",
    "last_login": "2026-02-06T10:05:00"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account is inactive

### Protected Endpoints (Require Authentication)

#### Get Profile
Get current user's profile.

**Endpoint:** `GET /profile`

**Headers:** `Authorization: Bearer <token>`

**Success Response:** `200 OK`
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true,
    "created_at": "2026-02-06T10:00:00",
    "updated_at": "2026-02-06T10:00:00",
    "last_login": "2026-02-06T10:05:00"
  }
}
```

#### Update Profile
Update current user's profile.

**Endpoint:** `PUT /profile`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "John Updated Doe"
}
```

**Success Response:** `200 OK`
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "newemail@example.com",
    "full_name": "John Updated Doe",
    ...
  }
}
```

#### Change Password
Change current user's password.

**Endpoint:** `POST /change-password`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "old_password": "SecurePass123",
  "new_password": "NewSecurePass123"
}
```

**Success Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `401 Unauthorized` - Incorrect old password
- `400 Bad Request` - New password doesn't meet requirements

### Admin Endpoints (Require Admin Role)

#### List All Users
Get list of all users.

**Endpoint:** `GET /users`

**Headers:** `Authorization: Bearer <admin_token>`

**Success Response:** `200 OK`
```json
{
  "users": [
    {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com",
      ...
    },
    {
      "id": 2,
      "username": "janedoe",
      "email": "jane@example.com",
      ...
    }
  ],
  "count": 2
}
```

**Error Response:**
- `403 Forbidden` - Not an admin user

#### Get User by ID
Get specific user details.

**Endpoint:** `GET /users/<user_id>`

**Headers:** `Authorization: Bearer <token>`

**Success Response:** `200 OK`
```json
{
  "user": {
    "id": 2,
    "username": "janedoe",
    "email": "jane@example.com",
    ...
  }
}
```

**Notes:** Users can view their own profile. Admins can view any user.

#### Update User
Update user role or status (Admin only).

**Endpoint:** `PUT /users/<user_id>`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "role": "admin",
  "is_active": true
}
```

**Success Response:** `200 OK`
```json
{
  "message": "User updated successfully",
  "user": {
    "id": 2,
    "username": "janedoe",
    "role": "admin",
    "is_active": true,
    ...
  }
}
```

#### Delete User
Delete a user (Admin only).

**Endpoint:** `DELETE /users/<user_id>`

**Headers:** `Authorization: Bearer <admin_token>`

**Success Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Cannot delete own account
- `403 Forbidden` - Not an admin user
- `404 Not Found` - User not found

## Error Handling

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Description of what went wrong"
}
```

### 401 Unauthorized
```json
{
  "msg": "Missing Authorization Header"
}
```
or
```json
{
  "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Unauthorized. Admin access required"
}
```

### 404 Not Found
```json
{
  "error": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Operation failed: <error details>"
}
```

## Testing with curl

### Register a new user
```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test1234",
    "full_name": "Test User"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test1234"
  }'
```

### Get profile (requires token from login)
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Update profile
```bash
curl -X PUT http://localhost:5000/api/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "email": "newemail@example.com"
  }'
```

### Change password
```bash
curl -X POST http://localhost:5000/api/change-password \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "Test1234",
    "new_password": "NewTest1234"
  }'
```
