import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.dashboard.utils.db import get_cities, get_historical_scores, get_raw_metrics

st.set_page_config(page_title="Historical Trends", page_icon="📈", layout="wide")
st.title("📈 Historical Trends")

cities      = get_cities()
city        = st.selectbox("Select city", cities)
period      = st.selectbox("Time period", ["30 days", "90 days", "180 days", "1 year", "All time"])
days_map    = {"30 days": 30, "90 days": 90, "180 days": 180, "1 year": 365, "All time": 99999}
days        = days_map[period]

df = get_historical_scores(city)
if days < 99999:
    df = df[df["date_id"] >= df["date_id"].max() - pd.Timedelta(days=days)]

st.subheader(f"Total Stress Score — {city}")
fig = px.line(df, x="date_id", y="score", height=350,
              labels={"date_id": "Date", "score": "Stress Score"})
fig.add_hrect(y0=0,  y1=25, fillcolor="green",  opacity=0.05, line_width=0)
fig.add_hrect(y0=25, y1=50, fillcolor="yellow", opacity=0.05, line_width=0)
fig.add_hrect(y0=50, y1=75, fillcolor="orange", opacity=0.05, line_width=0)
fig.add_hrect(y0=75, y1=100,fillcolor="red",    opacity=0.05, line_width=0)
fig.update_layout(margin=dict(t=20, b=20), yaxis=dict(range=[0, 100]))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Component Score Trends")
components  = ["traffic_score", "air_quality_score", "weather_score", "safety_score", "cost_score"]
comp_labels = {"traffic_score": "Traffic", "air_quality_score": "Air Quality",
               "weather_score": "Weather", "safety_score": "Safety", "cost_score": "Cost"}

selected_comp = st.multiselect(
    "Select components",
    options=components,
    default=components,
    format_func=lambda x: comp_labels[x],
)

if selected_comp:
    df_melt = df.melt(
        id_vars="date_id",
        value_vars=selected_comp,
        var_name="component",
        value_name="component_score",
    )
    df_melt["component"] = df_melt["component"].map(comp_labels)

    fig2 = px.line(
        df_melt,
        x="date_id",
        y="component_score",
        color="component",
        height=400,
        labels={"date_id": "Date", "component_score": "Score"},
    )
    fig2.update_layout(margin=dict(t=20, b=20), yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Raw Metrics")
df_raw = get_raw_metrics(city)
if days < 99999:
    df_raw = df_raw[df_raw["date_id"] >= df_raw["date_id"].max() - pd.Timedelta(days=days)]

metric = st.selectbox("Select raw metric", [
    "congestion_index", "avg_pm25", "aqi_estimate",
    "temp_c", "feels_like_c", "humidity_pct", "weather_stress", "crime_score", "cost_index"
])

fig3 = px.line(df_raw, x="date_id", y=metric, height=300,
               labels={"date_id": "Date", metric: metric.replace("_", " ").title()})
fig3.update_layout(margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Monthly Average Scores")
df["month"] = df["date_id"].dt.to_period("M").astype(str)
monthly = df.groupby("month")["score"].mean().reset_index()
monthly.columns = ["month", "avg_score"]
fig4 = px.bar(monthly, x="month", y="avg_score", height=300,
              labels={"month": "Month", "avg_score": "Avg Stress Score"})
fig4.update_layout(margin=dict(t=20, b=20))
st.plotly_chart(fig4, use_container_width=True)