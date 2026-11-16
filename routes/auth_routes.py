"""
Authentication API routes for Rainfall Intelligence.
Handles user registration, login, logout, profile update, and password change.
"""

from flask import Blueprint, request, jsonify, session
from services.auth_service import register_user, authenticate_user, get_current_user, login_required
from services.db import update_user_profile, update_user_password
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    
    success, msg, user = register_user(email, password, full_name)
    if not success:
        return jsonify({"success": False, "error": msg}), 400
        
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["full_name"]
    session["user_role"] = user.get("role", "user")
    session.permanent = True
    
    return jsonify({
        "success": True,
        "message": msg,
        "user": user
    }), 201

@auth_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    ip_addr = request.remote_addr or "127.0.0.1"
    
    success, msg, user = authenticate_user(email, password, ip_address=ip_addr)
    if not success:
        return jsonify({"success": False, "error": msg}), 401
        
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["full_name"]
    session["user_role"] = user.get("role", "user")
    session.permanent = True
    
    return jsonify({
        "success": True,
        "message": msg,
        "user": user
    }), 200

@auth_bp.route("/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Signed out successfully."}), 200

@auth_bp.route("/me", methods=["GET"])
def api_me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False, "user": None}), 200
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "user"),
            "created_at": user.get("created_at")
        }
    }), 200

@auth_bp.route("/profile", methods=["POST"])
@login_required
def api_update_profile():
    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name", "").strip()
    if not full_name or len(full_name) < 2:
        return jsonify({"success": False, "error": "Full name must be at least 2 characters."}), 400
        
    user_id = session.get("user_id")
    update_user_profile(user_id, full_name)
    session["user_name"] = full_name
    return jsonify({"success": True, "message": "Profile updated successfully.", "full_name": full_name}), 200

@auth_bp.route("/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.get_json(silent=True) or {}
    current_pwd = data.get("current_password", "")
    new_pwd = data.get("new_password", "")
    
    if len(new_pwd) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters long."}), 400
        
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404
        
    if not check_password_hash(user["password_hash"], current_pwd):
        return jsonify({"success": False, "error": "Current password is incorrect."}), 400
        
    new_hash = generate_password_hash(new_pwd)
    update_user_password(user["id"], new_hash)
    return jsonify({"success": True, "message": "Password changed successfully."}), 200
