import streamlit as st
import plotly.graph_objects as go
import sys, os

st.set_page_config(page_title="Methodology", page_icon="📋", layout="wide")
st.title("📋 Methodology")
st.markdown("How the City Stress Index is calculated.")

from src.dashboard.utils.styling import inject_css, chart_theme
inject_css()

st.subheader("Data Sources")
col1, col2, col3, col4, col5 = st.columns(5)
sources = [
    ("🚦", "Traffic", "TomTom API", "Live congestion index"),
    ("🌫️", "Air Quality", "OpenAQ v3", "PM2.5, NO2, AQI"),
    ("🌧️", "Weather", "Open-Meteo", "Temp, humidity, precipitation"),
    ("🏠", "Cost", "Numbeo", "Cost of living index"),
    ("🔒", "Safety", "City open data", "Crime incident rates"),
]
for col, (icon, name, api, desc) in zip([col1,col2,col3,col4,col5], sources):
    with col:
        st.markdown(f"**{icon} {name}**")
        st.caption(api)
        st.caption(desc)

st.divider()

st.subheader("Scoring Formula")
st.markdown("""
The City Stress Score is a **weighted composite index** ranging from 0 (no stress) to 100 (maximum stress).
""")

weights = {
    "Traffic":     0.35,
    "Air Quality": 0.25,
    "Weather":     0.20,
    "Safety":      0.10,
    "Cost":        0.10,
}

fig = go.Figure(go.Pie(
    labels=list(weights.keys()),
    values=[v * 100 for v in weights.values()],
    hole=0.4,
    marker_colors=["#378ADD", "#1D9E75", "#BA7517", "#E24B4A", "#7F77DD"],
))
fig.update_layout(height=350, margin=dict(t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
st.plotly_chart(chart_theme(fig), use_container_width=True)

st.latex(r"""
\text{Stress Score} = 0.35 \times \text{Traffic} + 0.25 \times \text{Air Quality} +
0.20 \times \text{Weather} + 0.10 \times \text{Safety} + 0.10 \times \text{Cost}
""")

st.divider()
st.subheader("Normalization")
st.markdown("""
Each component is normalized to a 0–100 scale using min-max scaling before weighting:
""")
st.latex(r"\text{Normalized Score} = \frac{x - x_{min}}{x_{max} - x_{min}} \times 100")

st.divider()
st.subheader("Stress Labels")
col1, col2, col3, col4 = st.columns(4)
labels = [
    ("Low",      "0–25",  "#2ecc71", "City is performing well across all metrics."),
    ("Moderate", "26–50", "#f39c12", "Some elevated stress in one or more areas."),
    ("High",     "51–75", "#e67e22", "Significant stress — multiple metrics elevated."),
    ("Critical", "76–100","#e74c3c", "Extreme stress levels across major metrics."),
]
for col, (label, rng, color, desc) in zip([col1,col2,col3,col4], labels):
    with col:
        st.markdown(
            f"<div style='padding:12px; background:{color}20; border-left:4px solid {color}; "
            f"border-radius:4px'><strong style='color:{color}'>{label}</strong><br/>"
            f"<span style='font-size:13px'>{rng}</span><br/>"
            f"<span style='font-size:12px; color:#666'>{desc}</span></div>",
            unsafe_allow_html=True,
        )

st.divider()
st.subheader("Analytics Models")
st.markdown("""
**Forecasting**
- ARIMA (2,1,2) — captures short-term autocorrelation in daily stress scores
- Prophet — captures weekly and yearly seasonality patterns

**Anomaly Detection**
- Z-Score — flags values more than 2.5 standard deviations from the city mean
- Isolation Forest — detects multivariate outliers across all metrics simultaneously

**Clustering**
- K-Means (k=3) — segments cities into Low / Moderate / High stress tiers based on average component scores

**Feature Engineering**
- 7-day and 30-day rolling averages for smoothing
- Week-over-week change percentage for trend detection
- Heat stress index using the Heat Index formula
- Comfort score based on temperature and humidity optimal ranges
""")

st.divider()
st.subheader("Limitations")
st.markdown("""
- Cost of living data is static (annual Numbeo figures) rather than truly real-time
- Safety data uses static estimates for London, Mumbai, and Tokyo due to API availability
- Traffic historical data is synthetically generated using city-specific profiles
- Forecasts are based on historical patterns and do not account for sudden events
""")

st.divider()
st.caption("Built by Bijal · Python · SQLite · Streamlit · Plotly · scikit-learn · Prophet · statsmodels")