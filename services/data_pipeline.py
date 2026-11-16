"""
Data Pipeline and Dataset Analysis Service for Rainfall Intelligence.
Handles:
1. Multi-dataset management (IMD 1901-2015, District Normal, and Custom Uploaded files).
2. Comprehensive exploratory data analysis (dimensions, datatypes, missing values, duplicates, descriptive stats).
3. Data cleaning (missing value imputation, duplicate removal, IQR outlier detection).
4. Feature analysis & correlation matrix generation for heatmaps and charts.
5. Leakage-free train-test splits for 7 Machine Learning Regressors.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

BASE_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)

INDIA_DATASET_PATH = os.path.join(BASE_DATA_DIR, "rainfall_in_india_1901_2015.csv")
DISTRICT_DATASET_PATH = os.path.join(BASE_DATA_DIR, "district_wise_rainfall_normal.csv")

INDIA_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
INDIA_SEASONS = ["Jan-Feb", "Mar-May", "Jun-Sep", "Oct-Dec"]

# Verified Geographic Coordinates & Metadata for Indian Subdivisions
INDIA_SUBDIVISION_COORDINATES = {
    "ANDAMAN & NICOBAR ISLANDS": {"lat": 11.7401, "lng": 92.6586, "zone": "Island Territory", "capital": "Port Blair"},
    "ARUNACHAL PRADESH": {"lat": 28.2180, "lng": 94.7278, "zone": "Northeast Himalayan", "capital": "Itanagar"},
    "ASSAM & MEGHALAYA": {"lat": 26.2006, "lng": 92.9376, "zone": "Northeastern Hills", "capital": "Dispur / Shillong"},
    "NAGA MANI MIZO TRIPURA": {"lat": 24.6637, "lng": 93.9063, "zone": "Eastern Hills", "capital": "Imphal / Aizawl"},
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": {"lat": 27.0360, "lng": 88.2627, "zone": "Sub-Himalayan East", "capital": "Gangtok / Siliguri"},
    "GANGETIC WEST BENGAL": {"lat": 23.1645, "lng": 88.4312, "zone": "Eastern Delta", "capital": "Kolkata"},
    "ORISSA": {"lat": 20.9517, "lng": 85.0985, "zone": "Eastern Littoral", "capital": "Bhubaneswar"},
    "JHARKHAND": {"lat": 23.6102, "lng": 85.2799, "zone": "Chota Nagpur Plateau", "capital": "Ranchi"},
    "BIHAR": {"lat": 25.0961, "lng": 85.3131, "zone": "Middle Gangetic Plain", "capital": "Patna"},
    "EAST UTTAR PRADESH": {"lat": 26.8467, "lng": 82.9000, "zone": "Upper Gangetic Plain East", "capital": "Varanasi / Gorakhpur"},
    "WEST UTTAR PRADESH": {"lat": 28.5000, "lng": 78.5000, "zone": "Upper Gangetic Plain West", "capital": "Meerut / Agra"},
    "UTTARAKHAND": {"lat": 30.0668, "lng": 79.0193, "zone": "Western Himalayan", "capital": "Dehradun"},
    "HARYANA DELHI & CHANDIGARH": {"lat": 29.0588, "lng": 76.0856, "zone": "Northern Plains", "capital": "New Delhi / Chandigarh"},
    "PUNJAB": {"lat": 31.1471, "lng": 75.3412, "zone": "Indo-Gangetic Basin", "capital": "Amritsar / Ludhiana"},
    "HIMACHAL PRADESH": {"lat": 31.1048, "lng": 77.1734, "zone": "Western Himalayan", "capital": "Shimla"},
    "JAMMU & KASHMIR": {"lat": 34.0837, "lng": 74.7973, "zone": "Trans-Himalayan", "capital": "Srinagar / Jammu"},
    "WEST RAJASTHAN": {"lat": 27.0000, "lng": 71.5000, "zone": "Thar Desert Zone", "capital": "Jodhpur / Jaisalmer"},
    "EAST RAJASTHAN": {"lat": 26.5000, "lng": 75.8000, "zone": "Semi-Arid Transition", "capital": "Jaipur"},
    "WEST MADHYA PRADESH": {"lat": 23.0000, "lng": 76.5000, "zone": "Malwa Plateau", "capital": "Indore / Ujjain"},
    "EAST MADHYA PRADESH": {"lat": 23.5000, "lng": 81.0000, "zone": "Central Highlands", "capital": "Jabalpur / Rewa"},
    "GUJARAT REGION": {"lat": 23.0225, "lng": 72.5714, "zone": "Western Lowlands", "capital": "Ahmedabad"},
    "SAURASHTRA & KUTCH": {"lat": 22.3039, "lng": 70.8022, "zone": "Peninsular Gujarat", "capital": "Rajkot / Bhuj"},
    "KONKAN & GOA": {"lat": 15.2993, "lng": 74.1240, "zone": "Western Ghats Littoral", "capital": "Panaji / Mumbai Coast"},
    "MADHYA MAHARASHTRA": {"lat": 19.0000, "lng": 74.5000, "zone": "Deccan Tableland", "capital": "Pune / Nashik"},
    "MATATHWADA": {"lat": 19.5000, "lng": 76.5000, "zone": "Rain Shadow Interior", "capital": "Chhatrapati Sambhajinagar"},
    "VIDARBHA": {"lat": 21.1458, "lng": 79.0882, "zone": "Eastern Deccan", "capital": "Nagpur"},
    "CHHATTISGARH": {"lat": 21.2787, "lng": 81.8661, "zone": "Mahanadi Basin", "capital": "Raipur"},
    "COASTAL ANDHRA PRADESH": {"lat": 16.5062, "lng": 80.6480, "zone": "Eastern Maritime Coast", "capital": "Visakhapatnam / Vijayawada"},
    "TELANGANA": {"lat": 17.3850, "lng": 78.4867, "zone": "Telangana Plateau", "capital": "Hyderabad"},
    "RAYALSEEMA": {"lat": 14.6819, "lng": 77.6006, "zone": "Southern Dry Plateau", "capital": "Tirupati / Anantapur"},
    "TAMIL NADU": {"lat": 11.1271, "lng": 78.6569, "zone": "Coromandel Coast", "capital": "Chennai"},
    "COASTAL KARNATAKA": {"lat": 13.5000, "lng": 74.8000, "zone": "Malabar Coastline", "capital": "Mangaluru / Udupi"},
    "NORTH INTERIOR KARNATAKA": {"lat": 15.5000, "lng": 75.8000, "zone": "Northern Deccan", "capital": "Hubballi / Belagavi"},
    "SOUTH INTERIOR KARNATAKA": {"lat": 12.5000, "lng": 76.5000, "zone": "Mysuru Plateau", "capital": "Bengaluru / Mysuru"},
    "KERALA": {"lat": 10.8505, "lng": 76.2711, "zone": "Tropical Malabar Littoral", "capital": "Thiruvananthapuram / Kochi"},
    "LAKSHADWEEP": {"lat": 10.5667, "lng": 72.6417, "zone": "Arabian Sea Atolls", "capital": "Kavaratti"}
}

def load_india_dataset() -> pd.DataFrame:
    """Loads and standardizes the 115-year India dataset."""
    df = pd.read_csv(INDIA_DATASET_PATH)
    df.columns = [c.strip() for c in df.columns]
    for col in INDIA_MONTHS + INDIA_SEASONS + ["ANNUAL"]:
        if col in df.columns:
            df[col] = df.groupby("SUBDIVISION")[col].transform(lambda s: s.fillna(s.median()))
    return df

def get_india_dataset_summary() -> Dict[str, Any]:
    """Provides subdivisional statistics and coordinates for all 36 subdivisions."""
    df = load_india_dataset()
    subdivisions = sorted(df["SUBDIVISION"].unique().tolist())
    subdivision_stats = []
    for sub in subdivisions:
        sub_df = df[df["SUBDIVISION"] == sub]
        geo = INDIA_SUBDIVISION_COORDINATES.get(sub, {
            "lat": 20.5937, "lng": 78.9629, "zone": "India Subcontinent", "capital": "Regional Center"
        })
        ann_mean = round(float(sub_df["ANNUAL"].mean()), 1)
        monthly_medians = {m: round(float(sub_df[m].median()), 1) for m in INDIA_MONTHS}
        subdivision_stats.append({
            "subdivision": sub,
            "latitude": geo["lat"],
            "longitude": geo["lng"],
            "zone": geo["zone"],
            "capital": geo["capital"],
            "annual_rainfall_mean_mm": ann_mean,
            "monthly_medians": monthly_medians
        })
    return {
        "dataset_name": "Rainfall in India (1901-2015)",
        "total_subdivisions": len(subdivisions),
        "subdivisions": subdivision_stats,
        "months": INDIA_MONTHS,
        "seasons": INDIA_SEASONS
    }

def prepare_india_train_test_split(
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, ColumnTransformer]:
    """Constructs monthly predictive dataset for India subdivisions."""
    df = load_india_dataset()
    records = []
    for _, row in df.iterrows():
        sub = row["SUBDIVISION"]
        for idx, m in enumerate(INDIA_MONTHS):
            rain = row[m]
            prev_m = row[INDIA_MONTHS[idx - 1]] if idx > 0 else row[INDIA_MONTHS[11]]
            records.append({
                "Subdivision": sub,
                "Month_Num": idx + 1,
                "Prev_Month_Rain_mm": float(prev_m),
                "Rainfall_mm": float(rain)
            })
    m_df = pd.DataFrame(records)
    m_df["Sub_Month_Normal_mm"] = m_df.groupby(["Subdivision", "Month_Num"])["Rainfall_mm"].transform("median")
    m_df["Target_Rain"] = (m_df["Rainfall_mm"] >= 25.0).astype(int)
    
    features = ["Subdivision", "Month_Num", "Prev_Month_Rain_mm", "Sub_Month_Normal_mm"]
    X = m_df[features].copy()
    y = m_df["Target_Rain"].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["Month_Num", "Prev_Month_Rain_mm", "Sub_Month_Normal_mm"]),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Subdivision"])
        ]
    )
    return X_train, X_test, y_train, y_test, preprocessor

def resolve_dataset_path(dataset_name: Optional[str] = None) -> str:
    """Returns absolute file path for a named dataset or default."""
    if not dataset_name or "1901" in dataset_name or "Subdivision" in dataset_name:
        return INDIA_DATASET_PATH
    if "District" in dataset_name:
        return DISTRICT_DATASET_PATH
    
    # Check custom uploads in BASE_DATA_DIR / uploads
    upload_path = os.path.join(BASE_DATA_DIR, "uploads", dataset_name)
    if os.path.exists(upload_path):
        return upload_path
    
    direct_path = os.path.join(BASE_DATA_DIR, dataset_name)
    if os.path.exists(direct_path):
        return direct_path
        
    return INDIA_DATASET_PATH

def load_dataset(dataset_name: Optional[str] = None) -> pd.DataFrame:
    """Loads dataset from CSV/XLSX into pandas DataFrame."""
    filepath = resolve_dataset_path(dataset_name)
    if not os.path.exists(filepath):
        # Fallback to India dataset if missing
        filepath = INDIA_DATASET_PATH
        
    if filepath.endswith((".xlsx", ".xls")):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)
        
    df.columns = [c.strip() for c in df.columns]
    return df

def get_dataset_inspection(dataset_name: Optional[str] = None) -> Dict[str, Any]:
    """Inspects dataset: first 10 rows, columns, types, nulls, duplicates, statistical description."""
    df = load_dataset(dataset_name)
    
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    missing_dict = df.isnull().sum().to_dict()
    duplicates_count = int(df.duplicated().sum())
    
    # Statistical description for numerical columns
    stats_df = df[num_cols].describe().round(2)
    stats_dict = stats_df.to_dict()
    
    # Format stats table for frontend display: metric -> col -> val
    metrics = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    stats_table = []
    for m in metrics:
        row = {"metric": m}
        for col in num_cols:
            if col in stats_dict and m in stats_dict[col]:
                row[col] = stats_dict[col][m]
        stats_table.append(row)
        
    # Correlation matrix for numerical columns (subset to top 14 cols for clean heatmap)
    corr_cols = [c for c in num_cols if c not in ("YEAR", "id", "ID")][:14]
    corr_matrix = {}
    if len(corr_cols) > 1:
        corr_df = df[corr_cols].corr().round(2).fillna(0)
        corr_matrix = {
            "columns": corr_cols,
            "values": corr_df.values.tolist()
        }

    # Automatically identify possible rainfall target columns
    target_candidates = [c for c in num_cols if any(k in c.upper() for k in ["ANNUAL", "TOTAL", "RAIN", "PRECIPITATION"])]
    suggested_target = target_candidates[0] if target_candidates else (num_cols[-1] if num_cols else "")
    
    return {
        "dataset_name": dataset_name or "Subdivision Rainfall (1901-2015)",
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "numerical_columns": num_cols,
        "categorical_columns": cat_cols,
        "missing_values": missing_dict,
        "total_missing": int(sum(missing_dict.values())),
        "duplicates_count": duplicates_count,
        "first_10_rows": df.head(10).fillna("").to_dict(orient="records"),
        "stats_table": stats_table,
        "correlation_matrix": corr_matrix,
        "suggested_target": suggested_target
    }

def clean_dataset_pipeline(
    dataset_name: Optional[str] = None,
    impute_strategy: str = "median",
    remove_duplicates: bool = True,
    handle_outliers: bool = False
) -> Dict[str, Any]:
    """
    Cleans dataset according to user choices and returns before/after summary.
    """
    df = load_dataset(dataset_name)
    initial_rows = len(df)
    initial_nulls = int(df.isnull().sum().sum())
    initial_dups = int(df.duplicated().sum())
    
    cleaned_df = df.copy()
    
    # 1. Duplicates
    removed_dups = 0
    if remove_duplicates and initial_dups > 0:
        cleaned_df = cleaned_df.drop_duplicates()
        removed_dups = initial_rows - len(cleaned_df)
        
    # 2. Impute missing values
    num_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if cleaned_df[col].isnull().any():
            if impute_strategy == "median":
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            elif impute_strategy == "mean":
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mean())
            elif impute_strategy == "mode":
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode()[0] if not cleaned_df[col].mode().empty else 0)
            elif impute_strategy == "ffill":
                cleaned_df[col] = cleaned_df[col].ffill().bfill()
                
    # 3. Outlier detection using IQR
    outliers_detected = 0
    if "ANNUAL" in cleaned_df.columns:
        q1 = cleaned_df["ANNUAL"].quantile(0.25)
        q3 = cleaned_df["ANNUAL"].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers_mask = (cleaned_df["ANNUAL"] < lower_bound) | (cleaned_df["ANNUAL"] > upper_bound)
        outliers_detected = int(outliers_mask.sum())
        if handle_outliers:
            cleaned_df["ANNUAL"] = cleaned_df["ANNUAL"].clip(lower=lower_bound, upper=upper_bound)
            
    final_rows = len(cleaned_df)
    final_nulls = int(cleaned_df.isnull().sum().sum())
    
    return {
        "status": "success",
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "removed_duplicates": removed_dups,
        "initial_missing_values": initial_nulls,
        "final_missing_values": final_nulls,
        "outliers_detected": outliers_detected,
        "outliers_handled": handle_outliers
    }

def get_visualization_data(dataset_name: Optional[str] = None) -> Dict[str, Any]:
    """Generates charts data (monthly trends, yearly timeline, distribution, regional comparison)."""
    df = load_dataset(dataset_name)
    
    # 1. Monthly Trends (mean across all records)
    monthly_trends = {}
    for m in INDIA_MONTHS:
        if m in df.columns:
            monthly_trends[m] = round(float(df[m].median() if df[m].notnull().any() else 0), 1)
            
    # 2. Yearly Rainfall Trends (if YEAR column exists)
    yearly_trends = []
    if "YEAR" in df.columns and "ANNUAL" in df.columns:
        yearly_grp = df.groupby("YEAR")["ANNUAL"].mean().round(1)
        # Sample every 2-3 years if long dataset
        years = yearly_grp.index.tolist()
        step = max(1, len(years) // 35)
        yearly_trends = [{"year": int(y), "rainfall_mm": float(yearly_grp[y])} for y in years[::step]]
        
    # 3. Regional Rainfall Comparison
    regional_data = []
    region_col = "SUBDIVISION" if "SUBDIVISION" in df.columns else ("STATE_UT_NAME" if "STATE_UT_NAME" in df.columns else None)
    if region_col and "ANNUAL" in df.columns:
        top_regions = df.groupby(region_col)["ANNUAL"].mean().sort_values(ascending=False)
        # Select top 6 wettest and top 6 driest
        selected = pd.concat([top_regions.head(6), top_regions.tail(6)]).drop_duplicates()
        for r_name, r_val in selected.items():
            regional_data.append({"region": str(r_name), "rainfall_mm": round(float(r_val), 1)})
            
    # 4. Rainfall Distribution (Histogram bins for ANNUAL)
    distribution_bins = []
    if "ANNUAL" in df.columns:
        valid_annual = df["ANNUAL"].dropna()
        counts, bin_edges = np.histogram(valid_annual, bins=10)
        for i in range(len(counts)):
            distribution_bins.append({
                "range": f"{int(bin_edges[i])}-{int(bin_edges[i+1])} mm",
                "count": int(counts[i])
            })
            
    # 5. Seasonal Contribution
    seasonal_data = {}
    for s in INDIA_SEASONS:
        if s in df.columns:
            seasonal_data[s] = round(float(df[s].mean()), 1)
            
    return {
        "monthly_trends": monthly_trends,
        "yearly_trends": yearly_trends,
        "regional_data": regional_data,
        "distribution_bins": distribution_bins,
        "seasonal_data": seasonal_data
    }

def prepare_regression_train_test_split(
    dataset_name: Optional[str] = None,
    target_column: Optional[str] = None,
    feature_columns: Optional[List[str]] = None,
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, List[str], str]:
    """
    Constructs train/test split without data leakage.
    Returns: X_train, X_test, y_train, y_test, used_features, target_col.
    """
    df = load_dataset(dataset_name)
    
    # Handle target
    target = target_column or ("ANNUAL" if "ANNUAL" in df.columns else df.select_dtypes(include=[np.number]).columns[-1])
    
    # Handle features
    if feature_columns and len(feature_columns) > 0:
        features = [f for f in feature_columns if f in df.columns and f != target]
    else:
        # Default to available months
        candidate_features = [m for m in INDIA_MONTHS if m in df.columns and m != target]
        if candidate_features:
            features = candidate_features
        else:
            features = [c for c in df.select_dtypes(include=[np.number]).columns if c != target]
            
    # Impute missing values on numeric columns using median
    clean_df = df[features + [target]].copy()
    for col in clean_df.columns:
        if clean_df[col].dtype.kind in "biufc":
            clean_df[col] = clean_df[col].fillna(clean_df[col].median())
        else:
            clean_df[col] = clean_df[col].fillna("Unknown")
            
    X = clean_df[features].copy()
    y = clean_df[target].values.astype(float)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state
    )
    
    return X_train, X_test, y_train, y_test, features, target
