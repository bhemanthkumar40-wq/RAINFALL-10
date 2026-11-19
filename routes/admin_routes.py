"""
Admin Dashboard API routes for Rainfall Intelligence.
Protected by admin_required authorization.
Provides user management, login auditing, system statistics, and reporting.
"""

import io
import csv
from flask import Blueprint, jsonify, request, Response
from services.auth_service import admin_required
from services.db import (
    get_all_users, toggle_user_active_status, set_user_role,
    delete_user, get_recent_login_logs, get_all_predictions,
    get_platform_stats
)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/stats", methods=["GET"])
@admin_required
def api_admin_stats():
    stats = get_platform_stats()
    return jsonify({"success": True, "stats": stats}), 200

@admin_bp.route("/users", methods=["GET"])
@admin_required
def api_admin_users():
    users = get_all_users()
    return jsonify({"success": True, "users": users}), 200

@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def api_toggle_user_status(user_id: int):
    new_status = toggle_user_active_status(user_id)
    if new_status is None:
        return jsonify({"success": False, "error": "User not found."}), 404
    return jsonify({
        "success": True,
        "user_id": user_id,
        "is_active": new_status,
        "message": f"User {'activated' if new_status == 1 else 'deactivated'} successfully."
    }), 200

@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@admin_required
def api_update_user_role(user_id: int):
    data = request.get_json(silent=True) or {}
    role = data.get("role", "user")
    success = set_user_role(user_id, role)
    if not success:
        return jsonify({"success": False, "error": "Failed to update role or invalid role."}), 400
    return jsonify({"success": True, "user_id": user_id, "role": role}), 200

@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def api_delete_user(user_id: int):
    success = delete_user(user_id)
    if not success:
        return jsonify({"success": False, "error": "User could not be deleted."}), 400
    return jsonify({"success": True, "message": "User deleted successfully."}), 200

@admin_bp.route("/login-logs", methods=["GET"])
@admin_required
def api_login_logs():
    limit = int(request.args.get("limit", 50))
    logs = get_recent_login_logs(limit=limit)
    return jsonify({"success": True, "logs": logs}), 200

@admin_bp.route("/predictions", methods=["GET"])
@admin_required
def api_admin_predictions():
    limit = int(request.args.get("limit", 100))
    predictions = get_all_predictions(limit=limit)
    return jsonify({"success": True, "predictions": predictions}), 200

@admin_bp.route("/export-report", methods=["GET"])
@admin_required
def api_export_admin_report():
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write summary header
    stats = get_platform_stats()
    writer.writerow(["RAINFALL INTELLIGENCE - SYSTEM AUDIT REPORT"])
    writer.writerow(["Total Registered Users", stats["total_users"]])
    writer.writerow(["Active Users", stats["active_users"]])
    writer.writerow(["Total Predictions Executed", stats["total_predictions"]])
    writer.writerow(["Managed Datasets", stats["total_datasets"]])
    writer.writerow([])
    
    # Write users section
    writer.writerow(["REGISTERED USERS"])
    writer.writerow(["User ID", "Full Name", "Email", "Role", "Active Status", "Predictions Made", "Registered Date"])
    for u in get_all_users():
        writer.writerow([
            u["id"], u["full_name"], u["email"], u["role"],
            "Active" if u["is_active"] else "Inactive",
            u["prediction_count"], u["created_at"]
        ])
    writer.writerow([])
    
    # Write recent login logs section
    writer.writerow(["RECENT LOGIN ATTEMPTS AUDIT"])
    writer.writerow(["Log ID", "Email", "IP Address", "Status", "Reason", "Timestamp"])
    for l in get_recent_login_logs(limit=100):
        writer.writerow([l["id"], l["email"], l["ip_address"], l["status"], l["reason"], l["created_at"]])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=rainfall_system_audit_report.csv"}
    )
