import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.dashboard.utils.db import get_cities, get_anomalies, get_historical_scores

st.set_page_config(page_title="Anomaly Detection", page_icon="🚨", layout="wide")
st.title("🚨 Anomaly Detection")
st.markdown("Unusual stress events detected using Z-Score and Isolation Forest models.")

from src.dashboard.utils.styling import inject_css, chart_theme
inject_css()

cities      = get_cities()
city        = st.selectbox("Select city", ["All cities"] + cities)
city_filter = None if city == "All cities" else city

df_anomalies = get_anomalies(city_filter)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Anomalies", len(df_anomalies))
with col2:
    spikes = len(df_anomalies[df_anomalies["anomaly_type"] == "spike"])
    st.metric("Spikes", spikes)
with col3:
    drops = len(df_anomalies[df_anomalies["anomaly_type"] == "drop"])
    st.metric("Drops", drops)

st.divider()

if not df_anomalies.empty:
    st.subheader("Anomalies Over Time")
    df_plot = df_anomalies.copy()
    df_plot["date_id"] = pd.to_datetime(df_plot["date_id"])

    fig = px.scatter(
        df_plot,
        x="date_id",
        y="value",
        color="city",
        symbol="anomaly_type",
        hover_data=["metric", "z_score", "anomaly_type"],
        height=400,
        labels={"date_id": "Date", "value": "Metric Value"},
    )
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(chart_theme(fig), use_container_width=True)
    
    st.subheader("Anomalies by Metric")
    metric_counts = df_anomalies["metric"].value_counts().reset_index()
    metric_counts.columns = ["metric", "count"]
    fig2 = px.bar(
        metric_counts,
        x="metric",
        y="count",
        height=300,
        labels={"metric": "Metric", "count": "Anomaly Count"},
        color="count",
        color_continuous_scale=["#2ecc71", "#e74c3c"],
    )
    fig2.update_layout(margin=dict(t=20, b=20), coloraxis_showscale=False)
    st.plotly_chart(chart_theme(fig2), use_container_width=True)

    if city != "All cities":
        st.subheader(f"Stress Score with Anomalies — {city}")
        hist_df = get_historical_scores(city)
        anomaly_dates = df_anomalies[df_anomalies["metric"] == "total_stress_score"]["date_id"]

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=hist_df["date_id"],
            y=hist_df["score"],
            name="Stress Score",
            line=dict(color="#378ADD"),
        ))

        anomaly_points = hist_df[hist_df["date_id"].isin(anomaly_dates)]
        fig3.add_trace(go.Scatter(
            x=anomaly_points["date_id"],
            y=anomaly_points["score"],
            mode="markers",
            marker=dict(color="#E24B4A", size=10, symbol="x"),
            name="Anomaly",
        ))

        fig3.update_layout(height=400, margin=dict(t=20, b=20),
                           yaxis=dict(range=[0, 100]))
        st.plotly_chart(chart_theme(fig3), use_container_width=True)

    st.subheader("Anomaly Log")
    display = df_anomalies[["city", "date_id", "metric", "value", "z_score", "anomaly_type"]].copy()
    display["date_id"] = display["date_id"].dt.strftime("%Y-%m-%d")
    display["value"]   = display["value"].round(2)
    display["z_score"] = display["z_score"].round(3)
    display.columns    = ["City", "Date", "Metric", "Value", "Z-Score", "Type"]
    st.dataframe(display.head(100), use_container_width=True, hide_index=True)
else:
    st.info("No anomalies found for the selected filter.")