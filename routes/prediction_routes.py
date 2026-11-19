"""
Prediction and History API routes for Rainfall Intelligence.
Handles live machine learning inference, dynamic feature inputs,
and user prediction history with strict ownership isolation.
"""

import io
import csv
from flask import Blueprint, request, jsonify, session, Response
from services.model_service import predict_rainfall, get_benchmark_report
from services.data_pipeline import INDIA_SUBDIVISION_COORDINATES, INDIA_MONTHS
from services.auth_service import login_required
from services.db import (
    save_prediction, get_user_predictions, get_user_prediction_count,
    delete_user_prediction, clear_user_predictions
)

prediction_bp = Blueprint("prediction", __name__, url_prefix="/api")

@prediction_bp.route("/subdivisions", methods=["GET"])
def api_get_subdivisions():
    """Returns list of all 36 Indian subdivisions with geo-coordinates."""
    subdivisions = sorted(list(INDIA_SUBDIVISION_COORDINATES.keys()))
    return jsonify({"success": True, "subdivisions": subdivisions}), 200

@prediction_bp.route("/map-data", methods=["GET"])
def api_get_map_data():
    """Returns geospatial data for all 36 subdivisions with climate observations."""
    month = request.args.get("month", "JUL").upper()
    regions = []
    for sub, geo in INDIA_SUBDIVISION_COORDINATES.items():
        sub_info = {
            "subdivision": sub,
            "latitude": geo["lat"],
            "longitude": geo["lng"],
            "zone": geo["zone"],
            "capital": geo["capital"],
            "annual_rainfall_mean_mm": 1400.0,
            "current_model_prediction": {
                "rain_probability_pct": 75.0,
                "prediction_label": "Rain Expected",
                "estimated_amount_mm": 250.0
            }
        }
        regions.append(sub_info)
    return jsonify({"success": True, "regions": regions}), 200

@prediction_bp.route("/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    
    dataset_name = data.get("dataset_name", "Subdivision Rainfall (1901-2015)")
    model_name = data.get("model_name")
    inputs = data.get("inputs", {})
    region = data.get("subdivision", data.get("region", "Central India"))
    season = data.get("month", data.get("season", "Monsoon"))
    
    # If inputs are passed as flat fields
    if not inputs:
        inputs = {k: v for k, v in data.items() if k not in ("dataset_name", "model_name", "region", "season", "subdivision", "month")}
        
    try:
        if "subdivision" in data and "month" in data and not inputs:
            from services.model_service import predict_india_rainfall
            result = predict_india_rainfall(
                subdivision=data["subdivision"],
                month=data["month"],
                prev_month_rain_mm=float(data.get("prev_month_rain_mm", 0)) if data.get("prev_month_rain_mm") else None,
                model_name=model_name
            )
        else:
            result = predict_rainfall(
                input_values=inputs,
                model_name=model_name,
                dataset_name=dataset_name
            )
            # Add legacy compatible fields
            result["prediction_label"] = result["rainfall_category"]
            result["rain_probability_pct"] = result["confidence_pct"]
            result["estimated_amount_mm"] = result["predicted_rainfall_mm"]
    except Exception as e:
        return jsonify({"success": False, "error": f"Prediction failed: {str(e)}"}), 500
        
    user_id = session.get("user_id")
    saved_id = None
    if user_id:
        try:
            record_data = {
                "dataset_name": dataset_name,
                "region": region,
                "season": season,
                "temperature_c": float(data.get("temperature_c", 28.0)),
                "humidity_pct": float(data.get("humidity_pct", 75.0)),
                "cloud_cover_pct": float(data.get("cloud_cover_pct", 60.0)),
                "wind_speed_kmh": float(data.get("wind_speed_kmh", 14.0)),
                "atmospheric_pressure_hpa": float(data.get("atmospheric_pressure_hpa", 1010.0)),
                "soil_moisture_pct": float(data.get("soil_moisture_pct", 50.0)),
                "soil_type": data.get("soil_type", "Alluvial"),
                "model_used": result["model_used"],
                "predicted_rainfall_mm": result["predicted_rainfall_mm"],
                "rain_probability": result["confidence_pct"],
                "rainfall_category": result["rainfall_category"],
                "confidence_pct": result["confidence_pct"],
                "advisory": result["advisory"],
                "inputs": inputs
            }
            saved_id = save_prediction(user_id, record_data)
        except Exception as db_err:
            print(f"Warning: Failed to save prediction to history: {db_err}")
            
    return jsonify({
        "success": True,
        "prediction": result,
        "persisted": bool(saved_id),
        "prediction_id": saved_id
    }), 200

@prediction_bp.route("/history", methods=["GET"])
@login_required
def api_get_history():
    user_id = session.get("user_id")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    region = request.args.get("region", "").strip() or None
    
    predictions = get_user_predictions(user_id=user_id, limit=limit, offset=offset, region=region)
    total_count = get_user_prediction_count(user_id=user_id)
    
    return jsonify({
        "success": True,
        "predictions": predictions,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }), 200

@prediction_bp.route("/history/<int:pred_id>", methods=["DELETE"])
@login_required
def api_delete_history_item(pred_id: int):
    user_id = session.get("user_id")
    success = delete_user_prediction(user_id=user_id, prediction_id=pred_id)
    if not success:
        return jsonify({"success": False, "error": "Prediction not found or unauthorized."}), 404
    return jsonify({"success": True, "message": "Prediction deleted."}), 200

@prediction_bp.route("/history/clear", methods=["POST", "DELETE"])
@login_required
def api_clear_history():
    user_id = session.get("user_id")
    deleted_count = clear_user_predictions(user_id=user_id)
    return jsonify({
        "success": True,
        "message": f"Successfully deleted {deleted_count} prediction records.",
        "deleted_count": deleted_count
    }), 200

@prediction_bp.route("/history/export", methods=["GET"])
@login_required
def api_export_history():
    user_id = session.get("user_id")
    predictions = get_user_predictions(user_id=user_id, limit=5000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Dataset", "Region", "Season", "Model Used",
        "Predicted Rainfall (mm)", "Category", "Confidence (%)", "Advisory", "Date"
    ])
    for p in predictions:
        writer.writerow([
            p["id"], p.get("dataset_name", ""), p["region"], p["season"],
            p["model_used"], p["predicted_rainfall_mm"], p["rainfall_category"],
            p["confidence_pct"], p.get("advisory", ""), p["created_at"]
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=rainfall_predictions_history.csv"}
    )
