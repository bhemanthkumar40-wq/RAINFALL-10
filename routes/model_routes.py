"""
Model evaluation, benchmark, and dataset inspection API routes.
Delivers genuine regression benchmarks for all 7 algorithms,
dataset uploads, exploratory data analysis, and visualization feeds.
"""

import os
from flask import Blueprint, jsonify, request, session
from werkzeug.utils import secure_filename
from services.model_service import get_benchmark_report, train_all_models
from services.data_pipeline import (
    get_dataset_inspection, clean_dataset_pipeline,
    get_visualization_data, BASE_DATA_DIR
)
from services.db import get_all_datasets, register_dataset, get_platform_stats

model_bp = Blueprint("models", __name__, url_prefix="/api")

UPLOAD_FOLDER = os.path.join(BASE_DATA_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@model_bp.route("/models", methods=["GET"])
def api_get_models():
    dataset_name = request.args.get("dataset", "Subdivision Rainfall (1901-2015)")
    try:
        report = get_benchmark_report(dataset_name)
        return jsonify({"success": True, "report": report}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@model_bp.route("/models/train", methods=["POST"])
def api_train_models():
    data = request.get_json(silent=True) or {}
    dataset_name = data.get("dataset_name", "Subdivision Rainfall (1901-2015)")
    target_column = data.get("target_column")
    feature_columns = data.get("feature_columns")
    
    test_size = float(data.get("test_size", 0.20))
    test_size = max(0.10, min(0.40, test_size))
    
    try:
        report = train_all_models(
            dataset_name=dataset_name,
            target_column=target_column,
            feature_columns=feature_columns,
            test_size=test_size
        )
        return jsonify({
            "success": True,
            "message": f"Successfully trained 7 algorithms on {dataset_name} with {int((1-test_size)*100)}/{int(test_size*100)} train/test split.",
            "report": report
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Model training failed: {str(e)}"}), 500

@model_bp.route("/datasets", methods=["GET"])
def api_get_datasets():
    datasets = get_all_datasets()
    return jsonify({"success": True, "datasets": datasets}), 200

@model_bp.route("/datasets/inspect", methods=["GET"])
def api_inspect_dataset():
    dataset_name = request.args.get("dataset", "Subdivision Rainfall (1901-2015)")
    try:
        inspection = get_dataset_inspection(dataset_name)
        return jsonify({"success": True, "inspection": inspection}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@model_bp.route("/datasets/clean", methods=["POST"])
def api_clean_dataset():
    data = request.get_json(silent=True) or {}
    dataset_name = data.get("dataset_name", "Subdivision Rainfall (1901-2015)")
    impute_strategy = data.get("impute_strategy", "median")
    remove_dups = bool(data.get("remove_duplicates", True))
    handle_outliers = bool(data.get("handle_outliers", False))
    
    try:
        clean_result = clean_dataset_pipeline(
            dataset_name=dataset_name,
            impute_strategy=impute_strategy,
            remove_duplicates=remove_dups,
            handle_outliers=handle_outliers
        )
        return jsonify({"success": True, "result": clean_result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@model_bp.route("/datasets/visualizations", methods=["GET"])
def api_get_visualizations():
    dataset_name = request.args.get("dataset", "Subdivision Rainfall (1901-2015)")
    try:
        viz_data = get_visualization_data(dataset_name)
        return jsonify({"success": True, "data": viz_data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@model_bp.route("/datasets/upload", methods=["POST"])
def api_upload_dataset():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Unsupported file format. Please upload CSV, XLSX, or XLS."}), 400
        
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    
    # Inspect uploaded file with pandas
    try:
        import pandas as pd
        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(save_path)
        else:
            df = pd.read_csv(save_path)
            
        rows_count = len(df)
        cols_count = len(df.columns)
        
        # Check target column
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not num_cols:
            return jsonify({"success": False, "error": "Dataset must contain at least one numerical column for rainfall prediction."}), 400
            
        target_candidates = [c for c in num_cols if any(k in c.upper() for k in ["ANNUAL", "TOTAL", "RAIN", "PRECIPITATION"])]
        target_col = target_candidates[0] if target_candidates else num_cols[-1]
        feature_cols = [c for c in num_cols if c != target_col]
        
        user_id = session.get("user_id")
        clean_name = filename.rsplit(".", 1)[0].replace("_", " ").title()
        
        register_dataset(
            name=clean_name,
            filename=filename,
            filepath=save_path,
            rows=rows_count,
            cols=cols_count,
            target_col=target_col,
            features=feature_cols,
            uploaded_by=user_id
        )
        
        return jsonify({
            "success": True,
            "message": f"Dataset '{clean_name}' ({rows_count:,} rows, {cols_count} columns) uploaded successfully.",
            "dataset": {
                "name": clean_name,
                "filename": filename,
                "rows_count": rows_count,
                "cols_count": cols_count,
                "target_col": target_col,
                "features": feature_cols
            }
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to process dataset: {str(e)}"}), 500
