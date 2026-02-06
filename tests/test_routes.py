import pytest
from app import app, db, bcrypt
from app.models import User


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test admin user
            admin = User(
                username='admin',
                email='admin@test.com',
                password_hash=bcrypt.generate_password_hash('Admin123').decode('utf-8'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_token(client):
    """Get authentication token for admin user"""
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'Admin123'
    })
    return response.json['access_token']


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'


def test_register_user(client):
    """Test user registration"""
    response = client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@gmail.com',
        'password': 'Test1234',
        'full_name': 'Test User'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'
    assert response.json['user']['username'] == 'testuser'


def test_register_duplicate_username(client):
    """Test registration with duplicate username"""
    client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test1@gmail.com',
        'password': 'Test1234'
    })
    
    response = client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test2@gmail.com',
        'password': 'Test1234'
    })
    assert response.status_code == 400
    assert 'already exists' in response.json['error']


def test_register_invalid_email(client):
    """Test registration with invalid email"""
    response = client.post('/api/register', json={
        'username': 'testuser',
        'email': 'invalid-email',
        'password': 'Test1234'
    })
    assert response.status_code == 400
    assert 'email' in response.json['error'].lower()


def test_register_weak_password(client):
    """Test registration with weak password"""
    response = client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@gmail.com',
        'password': 'weak'
    })
    assert response.status_code == 400
    assert 'password' in response.json['error'].lower()


def test_login(client):
    """Test user login"""
    # Register user first
    client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@gmail.com',
        'password': 'Test1234'
    })
    
    # Login
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'Test1234'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['user']['username'] == 'testuser'


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/api/login', json={
        'username': 'nonexistent',
        'password': 'WrongPass123'
    })
    assert response.status_code == 401


def test_get_profile(client, auth_token):
    """Test getting user profile"""
    response = client.get('/api/profile', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    assert response.json['user']['username'] == 'admin'


def test_update_profile(client, auth_token):
    """Test updating user profile"""
    response = client.put('/api/profile', 
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'full_name': 'Updated Admin',
            'email': 'newemail@test.com'
        }
    )
    assert response.status_code == 200
    assert response.json['user']['full_name'] == 'Updated Admin'


def test_change_password(client, auth_token):
    """Test changing password"""
    response = client.post('/api/change-password',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'old_password': 'Admin123',
            'new_password': 'NewAdmin123'
        }
    )
    assert response.status_code == 200
    assert response.json['message'] == 'Password changed successfully'


def test_list_users_as_admin(client, auth_token):
    """Test listing all users as admin"""
    response = client.get('/api/users', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    assert 'users' in response.json
    assert response.json['count'] >= 1


def test_unauthorized_access(client):
    """Test accessing protected endpoint without token"""
    response = client.get('/api/profile')
    assert response.status_code == 401
