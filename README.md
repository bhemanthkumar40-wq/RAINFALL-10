<<<<<<< HEAD
# 🌧️ Rainfall Analysis

An empirical weather intelligence and machine learning web application for predicting rainfall chances, evaluating climate precipitation trends, and visualizing meteorological risks across all **36 subdivisions of India**.

Created by **Hemanth_Kumar**.

---

## 📊 Dataset Integration: Kaggle "Rainfall in India" (1901–2015)

The platform is integrated with the official dataset from Kaggle:
👉 **[Kaggle: Rainfall in India (1901-2015) by Raj Anand](https://www.kaggle.com/datasets/rajanand/rainfall-in-india)**  
*Primary Source:* Indian Meteorological Department (IMD), Ministry of Earth Sciences, Government of India.

### Dataset Specifications:
- **Total Records:** 4,116 annual subdivision entries &bull; 49,392 monthly observation rows.
- **Geographic Coverage:** All 36 official IMD subdivisions across India (Andaman & Nicobar, Arunachal Pradesh, Assam & Meghalaya, Coastal Karnataka, Kerala, Konkan & Goa, Gangetic West Bengal, Bihar, Punjab, West Rajasthan, Tamil Nadu, Telangana, etc.).
- **Temporal Horizon:** 115 continuous years (1901 to 2015).
- **Supported Fields & Units:**
  - `SUBDIVISION` (Text): 36 regional meteorological subdivisions.
  - `YEAR` (Integer): Calendar year (1901–2015).
  - `JAN` through `DEC` (Continuous Real): Monthly rainfall in millimeters (mm).
  - `Jan-Feb` (mm): Winter season aggregate.
  - `Mar-May` (mm): Pre-monsoon / Summer aggregate.
  - `Jun-Sep` (mm): Southwest Monsoon aggregate (crucial agricultural lifecycle).
  - `Oct-Dec` (mm): Post-monsoon / Northeast Monsoon aggregate.
  - `ANNUAL` (mm): Total annual cumulative precipitation.

---

## 🧠 Machine Learning Algorithms & Measured Benchmarks

All models are trained on an **80% stratified training split (39,513 records)** and rigorously evaluated on the **identical 20% held-out test split (9,879 records)** with zero data leakage.

### Test Set Benchmark Results:

| Classification Algorithm | Accuracy | Precision | Recall (Sensitivity) | F1-Score | ROC-AUC | Specificity | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gradient Boosting (Selected)** | **88.37%** | **0.9215** | **0.8711** | **0.8956** | **0.9490** | **0.9000** | **Trained** |
| **Logistic Regression** | 88.46% | 0.9293 | 0.8642 | 0.8956 | 0.9457 | 0.9118 | Trained |
| **Random Forest** | 88.38% | 0.9235 | 0.8690 | 0.8954 | 0.9426 | 0.9029 | Trained |
| **Support Vector Machine (Calibrated)** | 88.22% | 0.9239 | 0.8655 | 0.8938 | 0.9437 | 0.9038 | Trained |
| **Decision Tree** | 87.85% | 0.9210 | 0.8618 | 0.8904 | 0.9438 | 0.9000 | Trained |
| **K-Nearest Neighbors** | 85.42% | 0.8767 | 0.8674 | 0.8720 | 0.9203 | 0.8369 | Trained |
| **Gaussian Naive Bayes** | 80.36% | 0.8244 | 0.8349 | 0.8296 | 0.8802 | 0.7621 | Trained |
| **XGBoost (Extreme Gradient Boosting)** | — | — | — | — | — | — | *Unavailable* |

### Model Selection & Tradeoff Rationale:
In rainfall prediction, relying on raw accuracy is misleading due to seasonal precipitation asymmetry. A model predicting "Dry" all year would achieve high accuracy in arid areas while completely failing to predict monsoon downpours. Therefore, **Gradient Boosting** is selected as the production model by optimizing the composite harmonic **F1-Score (0.8956)** and **ROC-AUC (0.9490)**, balancing false alarms against dangerous missed rainfall warnings.

### Unavailable Algorithm Disclosure:
- **XGBoost:** Marked as unavailable in the current Python environment because `xgboost` is not installed. To enable it, execute `pip install xgboost`. Scikit-Learn's **Gradient Boosting** and **Random Forest** serve as the primary ensemble alternatives.

---

## 🎨 Visual Identity & Architecture

- **Color Palette:** Deep navy space (`#070d18`, `#0c1427`) with rainfall-inspired cyan (`#38bdf8`), teal (`#2dd4bf`), and soft violet (`#818cf8`) accents.
- **Glassmorphic UI:** Frosted glass panels (`backdrop-filter: blur(16px)`), subtle neon borders, accessible contrast ratios exceeding WCAG AA standards.
- **Atmospheric Visuals:** Canvas ambient rain particle generator and rotating Doppler radar animation (with `@media (prefers-reduced-motion: reduce)` support).
- **Interactive Leaflet Map:** All 36 subdivisions mapped with exact geographical coordinates, historical climate statistics, and live model prediction on marker click.
- **Authentication & Security:** Secure signup/login with cryptographic password hashing (PBKDF2/Scrypt, never plaintext). Prediction history isolated by `user_id`.

---

## 🗂️ Project Structure

```
rainfall-analysis/
├── app.py                             # Flask application entrypoint & routing
├── requirements.txt                   # Production dependencies
├── .env.example                       # Environment variables template
├── data/
│   ├── rainfall_in_india_1901_2015.csv# Kaggle 115-year IMD dataset (36 subdivisions)
│   ├── weather_rainfall.csv           # Atmospheric sensor dataset
│   └── rainfall_app.db                # SQLite database (auto-initialized)
├── models/
│   └── saved_india_models.joblib      # Serialized trained model pipelines & cache
├── services/
│   ├── __init__.py
│   ├── db.py                          # SQLite database session & strict user ownership checks
│   ├── auth_service.py                # Cryptographic authentication & password hashing
│   ├── data_pipeline.py               # Dataset ingestion, validation, geographic coordinates & splits
│   └── model_service.py               # Multi-model training, evaluation & inference engine
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py                 # /api/auth/register, /login, /logout, /me
│   ├── prediction_routes.py           # /api/predict, /api/map-data, /api/history, /api/subdivisions
│   └── model_routes.py                # /api/models, /api/models/train, /api/dataset-info
├── static/
│   ├── css/
│   │   └── style.css                  # Deep navy glassmorphism & responsive layout
│   └── js/
│       ├── main.js                    # Canvas ambient rain & toast notifications
│       ├── dashboard.js               # Form sync, Leaflet map & animated SVG gauge
│       ├── models.js                  # Chart.js benchmarks & confusion matrix
│       └── history.js                 # Prediction logs, filtering & CSV export
├── templates/
│   ├── base.html                      # Layout with navbar, ambient canvas & footer
│   ├── index.html                     # Hero landing page with radar animation
│   ├── dashboard.html                 # Main prediction dashboard & interactive map
│   ├── models.html                    # Model performance benchmarks & comparison charts
│   ├── history.html                   # Authenticated user prediction history
│   ├── login.html                     # Secure sign in
│   ├── register.html                  # Secure user registration
│   ├── about.html                     # Scientific documentation & credits
│   ├── 404.html                       # Friendly 404 error page
│   └── 500.html                       # Friendly 500 error page
└── tests/
    ├── test_data_pipeline.py          # Dataset schema & split tests
    ├── test_model_service.py          # Machine learning benchmark tests
    ├── test_auth_and_db.py            # Password hashing & ownership isolation tests
    └── test_api_routes.py             # End-to-end Flask endpoint integration tests
```

---

## 🚀 Setup & Execution Guide

### 1. Set Workspace
Recommended workspace directory:
```powershell
Set-Location "C:\Users\bhema\.gemini\antigravity\scratch\rainfall-analysis"
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Automated Tests
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### 4. Start the Web Application
```powershell
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 👤 Project Credit

**Created by Hemanth_Kumar**  
*Rainfall Analysis &bull; Empirical Weather Science &amp; Predictive Machine Learning*
=======
# RAINFALL-10
>>>>>>> ffe3c8baf230d6048e980a3bad88f2ced7a3addc
