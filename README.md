# 🌧️ RAINFALL INTELLIGENCE
## Smart Rainfall Analysis & Machine Learning Prediction System

An enterprise-grade, modern, and responsive meteorological forecasting and climate analytics platform designed to analyze historical rainfall observations, predict precipitation, evaluate machine learning models, and empower agricultural planning.

Created by **Hemanth Kumar**.

---

## 🎨 Complete Light Theme Design System

The application strictly implements a **modern, bright, light-themed user interface** designed for professional scientific visualization and SaaS meteorological platforms:

| UI Element | Palette Hex | Visual Characteristic |
| :--- | :---: | :--- |
| **Main Page Background** | `#F5F7FB` | Soft, clean off-white canvas |
| **Sidebar Background** | `#FFFFFF` | Crisp white with subtle right border |
| **Top Header Background** | `#FFFFFF` | Fixed pure white header with breadcrumbs & avatar |
| **Dashboard Cards** | `#FFFFFF` | White cards with subtle borders & soft shadows |
| **Primary Blue** | `#2563EB` | Active nav indicators, primary buttons, trend lines |
| **Secondary Blue** | `#3B82F6` | Histogram bars, secondary accents, metric badges |
| **Teal Accent** | `#0D9488` | Environmental sensors, timeline trends, secondary highlights |
| **Main Typography** | `#172033` | Deep high-contrast slate text for optimal legibility |
| **Secondary Text** | `#64748B` | Refined slate for subtitles and metadata labels |
| **Borders & Dividers** | `#E5EAF1` | Crisp, ultra-clean separation borders |
| **Success Color** | `#16A34A` | Top model indicators, high confidence scores |
| **Warning Color** | `#D97706` | Heavy rain advisories, moderate deviations |
| **Error / Alert Color** | `#DC2626` | Torrential rain warnings, deactivated accounts |

> **Note on Dark Mode:** Dark mode is provided strictly as an optional secondary theme accessible via the top-header Sun/Moon toggle. The entire application defaults to the **100% Light Theme**.

---

## 🚀 Key Functional Modules

### 1. Split-Screen Authentication (First Page Experience)
- Opens to a split-screen login page with weather illustrations on the left and a white card on the right.
- Password show/hide toggle, "Remember Me", registration with full validation.
- Fast one-click demo credentials for instant evaluation:
  - **Administrator:** `admin@rainfall.org` (Password: `Admin@1234`)
  - **Regular User:** `bhemanthkumar40@gmail.com` (Password: `Admin@1234`)

### 2. Main Analytics Dashboard
- **8 Dynamic Statistic Cards:** Total Weather Records (4,116+), Average Rainfall (1,418.5 mm), Maximum Rainfall (4,142.0 mm), Minimum Rainfall (115.2 mm), Total Features (19), Available ML Models (7 Regressors), Best Performing Model (Linear Regression / Extra Trees / Random Forest), Latest Prediction status.
- **Interactive Light-Themed Chart.js Visualizations:**
  1. *Monthly Rainfall Trends:* Median precipitation across all 12 calendar months.
  2. *115-Year Climate Timeline (1901–2015):* Multi-decadal rainfall cycles and annual means.
  3. *Rainfall Distribution:* Histogram frequency bins for annual precipitation.
  4. *Regional Comparison:* Comparative bar chart of wettest vs driest subdivisions.
  5. *Actual vs Predicted Curve:* Side-by-side ground truth vs ML predictions.
  6. *Seasonal Contribution Doughnut:* Southwest Monsoon vs Post-Monsoon vs Pre-Monsoon vs Winter.

### 3. Rainfall Prediction Studio
- Dynamic parameter input form with preloaded regional baselines.
- Real-time inference using selected algorithm (Random Forest, Gradient Boosting, Linear Regression, Decision Tree, KNN, SVR, Extra Trees).
- Prediction output displayed with units (mm), IMD severity category badge, reliability percentage, and agricultural advisories.
- Automatic persistence to SQLite prediction history.

### 4. Machine Learning Model Laboratory & Comparison
- Complete benchmark table of all 7 regression models on held-out test splits:
  - $R^2$ Score (Coefficient of Determination)
  - Mean Absolute Error (MAE, in mm)
  - Mean Squared Error (MSE)
  - Root Mean Squared Error (RMSE, in mm)
  - Mean Absolute Percentage Error (MAPE, in %)
  - Training Time (seconds)
- Side-by-side $R^2$ and error bar charts.
- Point-by-point Actual vs Predicted tracking chart across 40 test observations.
- Interactive laboratory retraining panel with adjustable Train/Test split slider (e.g. 80/20, 70/30).

### 5. 4-Tab Deep Data Analysis
- **Tab 1 – Data Overview:** Dimensions, column names, data types, full parametric statistical summary (count, mean, std, min, 25%, 50%, 75%, max).
- **Tab 2 – Data Cleaning:** Configurable missing value imputation (median, mean, mode, ffill), duplicate detection & removal, outlier detection using IQR 1.5× rule.
- **Tab 3 – Data Visualization:** Pearson correlation matrix heatmap rendered with high-contrast color-coded cells.
- **Tab 4 – Feature Analysis:** Feature importance rankings from tree ensembles and correlation rankings against the Annual Rainfall target.

### 6. Dataset Management & Ingestion
- Ingestion of custom datasets supporting **CSV, XLSX, and XLS** formats via drag-and-drop.
- Auto-detection of numerical columns, categorical columns, and suggested rainfall target columns.
- Instant 10-row dataset schema preview table.

### 7. User Prediction History
- User ownership isolation: users only access their own prediction history.
- Search filter by region, model, or severity category.
- Record deletion, clear all history, and one-click CSV export.

### 8. System Administration Control Panel
- Accessible exclusively by users with the `admin` role.
- Platform KPIs: Total users, active users, total predictions executed, managed datasets.
- User management table with activation/deactivation toggle and deletion.
- Login attempt security audit logs capturing email, IP address, status, and failure diagnostics.
- One-click CSV export of the complete system audit report.

### 9. User Settings & About Documentation
- Profile full name editing, password changes with cryptographic hashing.
- Theme preference configuration.
- Detailed IMD meteorological science and subdivision documentation.

---

## 📊 Pre-Integrated Datasets

1. **Subdivision Rainfall in India (1901–2015):**
   - Source: Indian Meteorological Department (IMD) / Kaggle
   - Records: 4,116 rows &bull; 19 columns
   - Coverage: 36 subdivisions across 115 continuous calendar years.
2. **India District-Wise Normal Rainfall:**
   - Records: 641 district observations &bull; 19 columns
   - Coverage: District-level seasonal and annual precipitation normals.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.14, Flask 3.1
- **Database:** SQLite with relational integrity, foreign keys, and indexes
- **Security:** Werkzeug cryptographic password hashing, role-based authorization, login auditing
- **Machine Learning:** Scikit-Learn 1.9, Pandas 3.1, NumPy 2.5, SciPy 1.18, Joblib 1.6
- **Frontend:** HTML5, CSS3 Custom Light-Theme Design System, Vanilla JavaScript (ES6+), Chart.js 4.4

---

## 🏃 Quick Start & Run Instructions

### 1. Activate Environment & Run Application
```bash
# Navigate to the project directory
cd rainfall-analysis

# Run the Flask application
python app.py
```
The server will start at: `http://127.0.0.1:5000`

### 2. Default Login Credentials
- **Admin Account:**
  - Email: `admin@rainfall.org`
  - Password: `Admin@1234`
- **User Account:**
  - Email: `bhemanthkumar40@gmail.com`
  - Password: `Admin@1234`

### 3. Run Automated Test Suite
```bash
# Run all unit and integration tests (18 tests)
python -m unittest discover tests
```

---

## 👨‍💻 Author & Academic Credits
**Developed by Hemanth Kumar**  
Master of Computer Applications (MCA) Final Project  
Rainfall Intelligence System &bull; 2026
