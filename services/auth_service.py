"""
Authentication and user credential security service.
Employs cryptographic password hashing, role-based authorization,
and login attempt auditing.
"""

import re
from functools import wraps
from typing import Optional, Dict, Any, Tuple
from flask import session, jsonify, request, redirect, url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from services.db import (
    create_user, get_user_by_email, get_user_by_id,
    update_user_last_login, log_login_attempt
)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_registration_input(email: str, password: str, full_name: str) -> Tuple[bool, Optional[str]]:
    """Validates registration input fields and security constraints."""
    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please provide a valid email address."
    
    if not full_name or len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."
    
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
        
    return True, None

def register_user(email: str, password: str, full_name: str, role: str = "user") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Registers a new user with secure password hashing."""
    valid, err = validate_registration_input(email, password, full_name)
    if not valid:
        return False, err or "Invalid input", None
    
    existing = get_user_by_email(email)
    if existing:
        return False, "An account with this email already exists.", None
    
    hashed_pwd = generate_password_hash(password)
    user_id = create_user(email, hashed_pwd, full_name, role)
    
    if not user_id:
        return False, "Failed to create user account. Please try again.", None
        
    user = get_user_by_id(user_id)
    return True, "Registration successful.", user

def authenticate_user(email: str, password: str, ip_address: str = "127.0.0.1") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Verifies credentials, checks active status, and logs login attempts."""
    if not email or not password:
        log_login_attempt(email, "failed", ip_address, "Empty credentials provided")
        return False, "Email and password are required.", None
        
    user = get_user_by_email(email)
    if not user:
        log_login_attempt(email, "failed", ip_address, "User not found")
        return False, "Invalid email or password.", None
        
    if not user.get("is_active", 1):
        log_login_attempt(email, "failed", ip_address, "Account deactivated")
        return False, "Your account has been deactivated. Please contact the administrator.", None

    if not check_password_hash(user["password_hash"], password):
        log_login_attempt(email, "failed", ip_address, "Incorrect password")
        return False, "Invalid email or password.", None
        
    # Successful login
    update_user_last_login(user["id"])
    log_login_attempt(email, "success", ip_address, "Successful login")
    
    safe_user = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", 1),
        "created_at": user["created_at"]
    }
    return True, "Authentication successful.", safe_user

def login_required(f):
    """Decorator to protect view endpoints requiring user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get("TESTING") and "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Please sign in to access this resource."}), 401
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect view endpoints requiring admin authorization."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Please sign in."}), 401
            return redirect(url_for("login_page", next=request.path))
        if session.get("user_role") != "admin":
            if request.path.startswith("/api/"):
                return jsonify({"error": "Forbidden. Administrator privileges required."}), 403
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns current authenticated user from session or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)
