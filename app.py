"""
Rainfall Analysis Web Application
A polished, modern meteorological forecasting and ML intelligence platform.
Created by Hemanth_Kumar.
"""

import os
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, g

from services.db import init_db
from services.auth_service import get_current_user
from services.data_pipeline import get_dataset_summary, load_and_validate_dataset
from services.model_service import train_all_models, get_benchmark_report

from routes.auth_routes import auth_bp
from routes.prediction_routes import prediction_bp
from routes.model_routes import model_bp

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
    
    # Initialize SQLite database
    init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(model_bp)
    
    # Global template context processor
    @app.context_processor
    def inject_global_context():
        user = get_current_user()
        return {
            "current_user": user,
            "creator_credit": "Created by Hemanth_Kumar",
            "app_name": "Rainfall Analysis",
            "app_tagline": "Empirical Weather Intelligence & Predictive Machine Learning",
            "github_url": GITHUB_REPO_URL
        }
        
    # --- Frontend HTML Page Routes ---
    
    @app.route("/")
    def index():
        return render_template("index.html")
        
    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")
        
    @app.route("/models")
    def models_page():
        return render_template("models.html")
        
    @app.route("/history")
    def history_page():
        if "user_id" not in session:
            return redirect(url_for("login_page", next="/history"))
        return render_template("history.html")
        
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
        
    @app.route("/about")
    def about_page():
        return render_template("about.html")
        
    @app.route("/github")
    def redirect_github():
        """Redirects directly to the GitHub repository."""
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
    # Pre-train or warm cache on startup
    try:
        print("Initializing machine learning models...")
        train_all_models()
        print("Models initialized successfully.")
    except Exception as e:
        print(f"Startup training warning: {e}")
        
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
