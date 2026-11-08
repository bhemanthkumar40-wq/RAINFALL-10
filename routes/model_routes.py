"""
Model evaluation, benchmark, and dataset introspection API routes.
Delivers held-out test evaluations for all 7 algorithms on the Kaggle India dataset.
"""

from flask import Blueprint, jsonify, request
from services.model_service import get_india_benchmark_report, train_india_models
from services.data_pipeline import get_india_dataset_summary, DatasetValidationError

model_bp = Blueprint("models", __name__, url_prefix="/api")

@model_bp.route("/models", methods=["GET"])
def api_get_models():
    try:
        report = get_india_benchmark_report()
        return jsonify({"success": True, "report": report}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@model_bp.route("/models/train", methods=["POST"])
def api_train_models():
    try:
        report = train_india_models(force_retrain=True)
        return jsonify({
            "success": True,
            "message": "Models retrained successfully on the 115-year India dataset (9,879 held-out test evaluations).",
            "report": report
        }), 200
    except DatasetValidationError as dve:
        return jsonify({"success": False, "error": f"Dataset validation failed: {str(dve)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Model training failed: {str(e)}"}), 500

@model_bp.route("/dataset-info", methods=["GET"])
def api_dataset_info():
    try:
        summary = get_india_dataset_summary()
        return jsonify({"success": True, "summary": summary}), 200
    except DatasetValidationError as dve:
        return jsonify({"success": False, "error": str(dve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
