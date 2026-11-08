"""
Authentication and user credential security service.
Employs cryptographic password hashing (never plaintext), input validation,
and session management.
"""

import re
from functools import wraps
from typing import Optional, Dict, Any, Tuple
from flask import session, jsonify, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from services.db import create_user, get_user_by_email, get_user_by_id

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_registration_input(email: str, password: str, full_name: str) -> Tuple[bool, Optional[str]]:
    """Validates registration input fields and security constraints."""
    if not email or not EMAIL_REGEX.match(email.strip()):
        return False, "Please provide a valid email address."
    
    if not full_name or len(full_name.strip()) < 2:
        return False, "Full name must be at least 2 characters long."
    
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
        
    return True, None

def register_user(email: str, password: str, full_name: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Registers a new user with secure password hashing.
    Returns (success, message, user_dict).
    """
    valid, err = validate_registration_input(email, password, full_name)
    if not valid:
        return False, err or "Invalid input", None
    
    existing = get_user_by_email(email)
    if existing:
        return False, "An account with this email already exists.", None
    
    # Secure hash with scrypt/pbkdf2:sha256
    hashed_pwd = generate_password_hash(password)
    user_id = create_user(email, hashed_pwd, full_name)
    
    if not user_id:
        return False, "Failed to create user account. Please try again.", None
        
    user = get_user_by_id(user_id)
    return True, "Registration successful.", user

def authenticate_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Verifies user credentials against stored cryptographic hash.
    Constant-time comparison protects against timing attacks.
    """
    if not email or not password:
        return False, "Email and password are required.", None
        
    user = get_user_by_email(email)
    if not user:
        return False, "Invalid email or password.", None
        
    if not check_password_hash(user["password_hash"], password):
        return False, "Invalid email or password.", None
        
    # Return user without sensitive hash
    safe_user = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "created_at": user["created_at"]
    }
    return True, "Authentication successful.", safe_user

def login_required(f):
    """Decorator to protect view endpoints requiring user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Please sign in to access this resource."}), 401
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns the current authenticated user from session or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)
