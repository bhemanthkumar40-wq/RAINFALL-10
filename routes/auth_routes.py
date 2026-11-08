"""
Authentication API routes for Rainfall Analysis.
Provides user registration, login, logout, and session inspection.
"""

from flask import Blueprint, request, jsonify, session
from services.auth_service import register_user, authenticate_user, get_current_user

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
        
    # Set session
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["full_name"]
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
    
    success, msg, user = authenticate_user(email, password)
    if not success:
        return jsonify({"success": False, "error": msg}), 401
        
    # Set session
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["full_name"]
    session.permanent = True
    
    return jsonify({
        "success": True,
        "message": msg,
        "user": user
    }), 200

@auth_bp.route("/logout", methods=["POST"])
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
            "created_at": user["created_at"]
        }
    }), 200
