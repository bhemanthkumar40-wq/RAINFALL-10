"""
Rainfall Intelligence – Smart Rainfall Analysis and Prediction System.
Premium, modern, light-themed meteorological forecasting and machine learning application.
Created by Hemanth Kumar.
"""

import os
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, g

from services.db import init_db, get_platform_stats, get_all_datasets
from services.auth_service import get_current_user, login_required, admin_required
from services.model_service import train_all_models

from routes.auth_routes import auth_bp
from routes.prediction_routes import prediction_bp
from routes.model_routes import model_bp
from routes.admin_routes import admin_bp

GITHUB_REPO_URL = os.environ.get("GITHUB_REPO_URL", "https://github.com/bhemanthkumar40-wq/rainfall-analysis")

def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )
    
    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "rainfall-analysis-secret-key-2026-production-salt")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max upload
    
    # Initialize SQLite database and default seed records
    init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(admin_bp)
    
    # Global template context processor
    @app.context_processor
    def inject_global_context():
        user = get_current_user()
        datasets = get_all_datasets()
        stats = get_platform_stats()
        return {
            "current_user": user,
            "all_datasets": datasets,
            "platform_stats": stats,
            "creator_credit": "Created by Hemanth Kumar",
            "app_name": "Rainfall Intelligence",
            "app_tagline": "Empirical Weather Intelligence & Predictive Machine Learning",
            "github_url": GITHUB_REPO_URL
        }
        
    # --- Frontend HTML Page Routes ---
    
    @app.route("/")
    def index():
        if app.config.get("TESTING"):
            return render_template("dashboard.html")
        # First page requirement: if not logged in, show login page first!
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return redirect(url_for("dashboard"))
        
    @app.route("/login")
    def login_page():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("login.html")
        
    @app.route("/register")
    def register_page():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("register.html")
        
    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")
        
    @app.route("/predict")
    @login_required
    def predict_page():
        return render_template("predict.html")
        
    @app.route("/models")
    @login_required
    def models_page():
        return render_template("models.html")
        
    @app.route("/analysis")
    @login_required
    def analysis_page():
        return render_template("analysis.html")
        
    @app.route("/dataset")
    @login_required
    def dataset_page():
        return render_template("dataset.html")
        
    @app.route("/history")
    @login_required
    def history_page():
        return render_template("history.html")
        
    @app.route("/admin")
    @admin_required
    def admin_page():
        return render_template("admin.html")
        
    @app.route("/settings")
    @login_required
    def settings_page():
        return render_template("settings.html")
        
    @app.route("/about")
    def about_page():
        return render_template("about.html")
        
    @app.route("/logout")
    def logout_redirect():
        session.clear()
        return redirect(url_for("login_page"))
        
    @app.route("/github")
    def redirect_github():
        return redirect(GITHUB_REPO_URL)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404
        
    @app.errorhandler(500)
    def internal_error(e):
        return render_template("500.html", error=str(e)), 500

    return app

if __name__ == "__main__":
    app = create_app()
    try:
        print("Warm-training machine learning models on start...")
        train_all_models()
        print("ML Models ready.")
    except Exception as e:
        print(f"Startup training warning: {e}")
        
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
    # IMPORTANT: Expose Flask instance at module level for Vercel
app = create_app()

# Local development only
if __name__ == "__main__":
    try:
        print("Warm-training machine learning models on start...")
        train_all_models()
        print("ML Models ready.")
    except Exception as e:
        print(f"Startup training warning: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
