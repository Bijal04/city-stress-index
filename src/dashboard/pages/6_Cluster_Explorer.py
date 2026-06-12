import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.dashboard.utils.db import get_clusters, get_all_historical_scores

st.set_page_config(page_title="Cluster Explorer", page_icon="🗂️", layout="wide")
st.title("🗂️ City Cluster Explorer")
st.markdown("Cities segmented into stress tiers using K-Means clustering.")

df = get_clusters()

CLUSTER_COLORS = {
    "Low Stress":      "#2ecc71",
    "Moderate Stress": "#f39c12",
    "High Stress":     "#e74c3c",
}

st.subheader("City Clusters")
for cluster_name in ["Low Stress", "Moderate Stress", "High Stress"]:
    cluster_cities = df[df["cluster_name"] == cluster_name]
    if cluster_cities.empty:
        continue

    color = CLUSTER_COLORS.get(cluster_name, "#888")
    st.markdown(
        f"<div style='padding:8px 16px; background:{color}20; border-left:4px solid {color}; "
        f"border-radius:4px; margin-bottom:8px'>"
        f"<strong style='color:{color}'>{cluster_name}</strong> — "
        f"{', '.join(cluster_cities['city'].tolist())}</div>",
        unsafe_allow_html=True,
    )

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cluster Comparison — Avg Scores")
    fig = px.bar(
        df,
        x="city",
        y="avg_stress_score",
        color="cluster_name",
        color_discrete_map=CLUSTER_COLORS,
        height=350,
        labels={"city": "City", "avg_stress_score": "Avg Stress Score", "cluster_name": "Cluster"},
        text="avg_stress_score",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(margin=dict(t=20, b=20), yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Feature Comparison by Cluster")
    features    = ["avg_traffic", "avg_air_quality", "avg_weather"]
    feat_labels = ["Traffic", "Air Quality", "Weather"]

    fig2 = go.Figure()
    for _, row in df.iterrows():
        color = CLUSTER_COLORS.get(row["cluster_name"], "#888")
        values = [row.get(f, 0) for f in features]
        values += [values[0]]
        fig2.add_trace(go.Scatterpolar(
            r=values,
            theta=feat_labels + [feat_labels[0]],
            fill="toself",
            name=row["city"],
            opacity=0.6,
        ))

    fig2.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=350,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Historical Score by Cluster")
hist_df = get_all_historical_scores()
hist_df = hist_df.merge(df[["city", "cluster_name"]], on="city", how="left")
last_90 = hist_df[hist_df["date_id"] >= hist_df["date_id"].max() - pd.Timedelta(days=90)]

cluster_avg = last_90.groupby(["date_id", "cluster_name"])["score"].mean().reset_index()
fig3 = px.line(
    cluster_avg,
    x="date_id",
    y="score",
    color="cluster_name",
    color_discrete_map=CLUSTER_COLORS,
    height=400,
    labels={"date_id": "Date", "score": "Avg Stress Score", "cluster_name": "Cluster"},
)
fig3.update_layout(margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Cluster Details")
st.dataframe(
    df[["city", "cluster_name", "avg_stress_score", "avg_traffic", "avg_air_quality", "avg_weather"]].round(2),
    use_container_width=True,
    hide_index=True,
)