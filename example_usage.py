#!/usr/bin/env python3
"""
Example usage script for the User Account Management System
This script demonstrates how to interact with the API
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def print_response(response, title="Response"):
    """Pretty print API response"""
    print(f"\n{title}:")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("-" * 50)

def main():
    print("=" * 50)
    print("User Account Management System - Example Usage")
    print("=" * 50)
    
    # 1. Health Check
    print("\n1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    
    # 2. Register a new user
    print("\n2. Register New User")
    user_data = {
        "username": "johndoe",
        "email": "john@test.com",
        "password": "SecurePass123",
        "full_name": "John Doe"
    }
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    print_response(response, "User Registration")
    
    # 3. Login
    print("\n3. User Login")
    login_data = {
        "username": "johndoe",
        "password": "SecurePass123"
    }
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print_response(response, "User Login")
    
    # Get access token
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 4. Get Profile
        print("\n4. Get User Profile")
        response = requests.get(f"{BASE_URL}/profile", headers=headers)
        print_response(response, "User Profile")
        
        # 5. Update Profile
        print("\n5. Update User Profile")
        update_data = {
            "full_name": "John Updated Doe",
            "email": "johnupdated@test.com"
        }
        response = requests.put(f"{BASE_URL}/profile", json=update_data, headers=headers)
        print_response(response, "Profile Update")
        
        # 6. Change Password
        print("\n6. Change Password")
        password_data = {
            "old_password": "SecurePass123",
            "new_password": "NewSecurePass123"
        }
        response = requests.post(f"{BASE_URL}/change-password", json=password_data, headers=headers)
        print_response(response, "Password Change")
    
    # 7. Register admin user (for demo purposes)
    print("\n7. Register Admin User")
    admin_data = {
        "username": "admin",
        "email": "admin@test.com",
        "password": "AdminPass123",
        "full_name": "System Admin"
    }
    response = requests.post(f"{BASE_URL}/register", json=admin_data)
    print_response(response, "Admin Registration")
    
    # 8. Login as admin
    print("\n8. Admin Login")
    admin_login = {
        "username": "admin",
        "password": "AdminPass123"
    }
    response = requests.post(f"{BASE_URL}/login", json=admin_login)
    
    if response.status_code == 200:
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Note: In a real system, you'd need to manually set the admin role in the database
        # For this demo, we'll just show what the endpoints look like
        
        # 9. List all users (admin only)
        print("\n9. List All Users (Admin)")
        response = requests.get(f"{BASE_URL}/users", headers=admin_headers)
        print_response(response, "List Users")
    
    # 10. Test invalid credentials
    print("\n10. Test Invalid Login")
    invalid_login = {
        "username": "invalid",
        "password": "WrongPass123"
    }
    response = requests.post(f"{BASE_URL}/login", json=invalid_login)
    print_response(response, "Invalid Login")
    
    # 11. Test weak password
    print("\n11. Test Weak Password Registration")
    weak_password_user = {
        "username": "weakuser",
        "email": "weak@test.com",
        "password": "weak"
    }
    response = requests.post(f"{BASE_URL}/register", json=weak_password_user)
    print_response(response, "Weak Password Registration")
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("=" * 50)

if __name__ == "__main__":
    print("Make sure the Flask server is running on http://localhost:5000")
    print("You can start it with: python run.py")
    time.sleep(2)
    
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Please make sure the Flask application is running.")
        print("Start it with: python run.py")
    except Exception as e:
        print(f"\nError: {e}")
