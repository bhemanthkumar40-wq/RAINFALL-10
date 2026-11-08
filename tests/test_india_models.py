import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.model_service import train_india_models, predict_india_rainfall, get_india_benchmark_report

def run_checks():
    print("Training India models on Kaggle dataset...")
    rep = train_india_models()
    print("Selected Best Model:", rep["selected_model_name"])
    print("\nBenchmark Evaluation Results on Held-out Test Data (9,879 records):")
    for m in rep["metrics"]:
        print(f"  {m['model_name']:24}: Acc={m['accuracy']:.4f}, Prec={m['precision']:.4f}, Rec={m['recall']:.4f}, F1={m['f1_score']:.4f}, AUC={m['roc_auc']:.4f}")
        
    print("\nUnavailable Algorithms:")
    for u in rep["unavailable_models"]:
        print(f"  {u['name']}: {u['reason']}")
        
    print("\n--- Testing Predictions ---")
    kerala_jul = predict_india_rainfall("KERALA", "JUL")
    print("Kerala (July Monsoon):", kerala_jul["prediction_label"], f"{kerala_jul['rain_probability_pct']}% chance", f"Est: {kerala_jul['estimated_amount_mm']} mm")
    
    raj_jan = predict_india_rainfall("WEST RAJASTHAN", "JAN")
    print("West Rajasthan (January Winter):", raj_jan["prediction_label"], f"{raj_jan['rain_probability_pct']}% chance", f"Est: {raj_jan['estimated_amount_mm']} mm")
    
    karnataka_aug = predict_india_rainfall("COASTAL KARNATAKA", "AUG")
    print("Coastal Karnataka (August):", karnataka_aug["prediction_label"], f"{karnataka_aug['rain_probability_pct']}% chance", f"Est: {karnataka_aug['estimated_amount_mm']} mm")
    
    bengal_sep = predict_india_rainfall("GANGETIC WEST BENGAL", "SEP")
    print("Gangetic West Bengal (September):", bengal_sep["prediction_label"], f"{bengal_sep['rain_probability_pct']}% chance", f"Est: {bengal_sep['estimated_amount_mm']} mm")

if __name__ == "__main__":
    run_checks()
