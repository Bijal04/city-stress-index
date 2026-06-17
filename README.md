# 🏙️ City Stress Index

A real-time urban health intelligence platform that scores city stress daily across 5 global cities using a weighted composite index built from traffic, air quality, weather, cost of living, and safety data.

**Live Dashboard →** [city-stress-index.streamlit.app](https://city-stress-index.streamlit.app)

---

## 📊 What It Does

The City Stress Index collects data from 5 APIs daily, normalizes each metric to a 0–100 scale, applies a weighted formula, and produces a single stress score per city per day. The dashboard visualizes rankings, trends, forecasts, anomalies, and city clusters.

**Cities covered:** Toronto · New York · London · Mumbai · Tokyo

**Stress Score Formula:**
Score = 35% Traffic + 25% Air Quality + 20% Weather + 10% Safety + 10% Cost of Living

**Score Labels:**
- 🟢 0–25: Low
- 🟡 26–50: Moderate  
- 🟠 51–75: High
- 🔴 76–100: Critical

---

## 🏗️ Architecture
Data Sources (5 APIs)

↓

Data Collectors (Python)

↓

SQLite Data Warehouse (Star Schema)

↓

Feature Engineering (Pandas + NumPy)

↓

Stress Index Engine (Weighted Scoring)

↓

Advanced Analytics (ARIMA · Prophet · Isolation Forest · K-Means)

↓

Streamlit Dashboard (7 pages)

↓

GitHub Actions (Daily automation at 06:00 UTC)

---

## 📡 Data Sources

| Source | Data | API |
|--------|------|-----|
| TomTom | Traffic congestion index | TomTom Traffic API |
| OpenAQ v3 | PM2.5, NO2, AQI | OpenAQ API |
| Open-Meteo | Historical weather | Open-Meteo Archive API |
| Numbeo | Cost of living index | Web scraping + static |
| City Open Data | Crime incidents | Toronto ArcGIS · NYC Open Data |

---

## 🗄️ Database Design (Star Schema)
fact_city_metrics     ← one row per city per day (all raw metrics)

|

├── dim_city    ← 5 cities reference table

├── dim_date    ← calendar dimension (year, month, season, quarter)

|

city_stress_scores    ← computed stress scores per city per day

city_features         ← engineered features (rolling avgs, trends, volatility)

city_rankings         ← daily city rankings with rank change tracking

city_forecasts        ← ARIMA + Prophet 30-day forecasts

city_anomalies        ← Z-Score + Isolation Forest anomaly flags

city_clusters         ← K-Means city segmentation results

**Dataset size:** 4,400+ rows · 5 cities · 890 days · 9 tables

---

## 📈 Dashboard Pages

| Page | Description |
|------|-------------|
| 🏠 Home | Live stress score cards + 30-day trend |
| 🏆 Rankings | City rankings history + score distribution |
| 🏙️ City Comparison | Radar chart + side-by-side breakdown |
| 📈 Historical Trends | Component drilldowns + monthly averages |
| 🔮 Forecasts | ARIMA + Prophet 30-day predictions |
| 🚨 Anomaly Detection | Z-Score + Isolation Forest flagged events |
| 🗂️ Cluster Explorer | K-Means city segmentation |
| 📋 Methodology | Full formula + data sources + limitations |

---

## 🤖 Analytics Models

**Forecasting**
- ARIMA (2,1,2) — short-term autocorrelation in daily stress scores
- Prophet — weekly and yearly seasonality patterns

**Anomaly Detection**
- Z-Score — flags values 2.5+ standard deviations from city mean
- Isolation Forest — multivariate outlier detection across all metrics

**Clustering**
- K-Means (k=3) — segments cities into Low / Moderate / High stress tiers

**Feature Engineering**
- 7-day and 30-day rolling averages
- Week-over-week % change
- Traffic volatility score
- Heat stress index (Heat Index formula)
- Comfort score (temperature + humidity)

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Data collection | requests, BeautifulSoup4 |
| Data processing | pandas, NumPy |
| Database | SQLite (star schema) |
| Feature engineering | pandas, NumPy, SciPy |
| ML / Analytics | scikit-learn, statsmodels, Prophet |
| Dashboard | Streamlit, Plotly |
| Automation | GitHub Actions (daily cron) |
| Deployment | Streamlit Cloud |
| Testing | pytest |
| Version control | Git + GitHub |

---

## 🚀 Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/city-stress-index.git
cd city-stress-index
```

**2. Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up API keys**
```bash
cp .env.example .env
# Fill in your API keys in .env
```

**5. Initialize database and backfill history**
```bash
python src/database.py
python src/load_dimensions.py
python src/run_backfill.py
```

**6. Run feature engineering and scoring**
```bash
python src/feature_engineering.py
python src/scoring_engine.py
python src/analytics/run_analytics.py
```

**7. Launch dashboard**
```bash
streamlit run src/dashboard/app.py
```

---

## 🔄 Daily Pipeline

The full pipeline runs automatically every day at 06:00 UTC via GitHub Actions:
Collect APIs → ETL → Feature Engineering → Scoring → Analytics → Quality Checks

To run manually:
```bash
python src/collectors/run_all.py
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

22 tests covering database integrity, scoring logic, and data collectors.

---

## 📁 Project Structure
city-stress-index/

├── src/

│   ├── collectors/          # 5 API data collectors

│   ├── analytics/           # rankings, forecasting, anomaly, clustering

│   ├── dashboard/           # 7-page Streamlit app

│   ├── database.py          # SQLite schema

│   ├── etl_loader.py        # JSON → SQLite ETL

│   ├── feature_engineering.py

│   ├── scoring_engine.py

│   ├── run_backfill.py

│   ├── data_quality.py

│   └── logger.py

├── data/

│   └── raw/                 # daily API response JSON files

├── tests/                   # pytest test suite

├── logs/                    # pipeline run logs

├── .github/workflows/       # GitHub Actions CI/CD

├── config.yaml              # scoring weights

└── requirements.txt

---

## 🔑 API Keys Required

| API | Free tier | Sign up |
|-----|-----------|---------|
| TomTom | ✅ Yes | developer.tomtom.com |
| OpenWeatherMap | ✅ Yes | openweathermap.org |
| OpenAQ | ✅ Yes | api.openaq.org |
| Open-Meteo | ✅ No key needed | open-meteo.com |

---

## ⚠️ Limitations

- Cost of living data is static annual figures from Numbeo (not truly real-time)
- Safety data uses static estimates for London, Mumbai, Tokyo
- Historical traffic data is synthetically generated using city profiles
- Forecasts are pattern-based and don't account for sudden events

---

## 👩‍💻 Author

Built by **Bijal** as a portfolio project demonstrating full-stack data engineering and analytics.

**Skills demonstrated:** API integration · Web scraping · ETL pipelines · Data warehousing · Feature engineering · Statistical forecasting · Anomaly detection · Clustering · Dashboard development · CI/CD automation · Testing