import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.dashboard.utils.db import get_latest_scores, get_all_historical_scores

st.set_page_config(
    page_title="City Stress Index",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

LABEL_COLORS = {
    "Low":      "#2ecc71",
    "Moderate": "#f39c12",
    "High":     "#e67e22",
    "Critical": "#e74c3c",
}

st.title("🏙️ City Stress Index")
st.markdown("A real-time urban health intelligence platform scoring city stress across traffic, air quality, weather, safety, and cost of living.")

st.divider()

df = get_latest_scores()

if df.empty:
    st.warning("No data available. Run the pipeline first.")
    st.stop()

latest_date = df["date_id"].max()
st.caption(f"Last updated: {latest_date}")

st.subheader("Today's City Stress Rankings")

cols = st.columns(len(df))
for i, (_, row) in enumerate(df.iterrows()):
    with cols[i]:
        color = LABEL_COLORS.get(row["label"], "#888")
        st.metric(
            label=row["city"],
            value=f"{row['score']:.1f}",
            delta=row["label"],
        )
        st.markdown(
            f"<div style='text-align:center; color:{color}; font-weight:500; font-size:13px'>● {row['label']}</div>",
            unsafe_allow_html=True,
        )

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Stress Score Breakdown")
    components = ["traffic_score", "air_quality_score", "weather_score", "safety_score", "cost_score"]
    labels     = ["Traffic", "Air Quality", "Weather", "Safety", "Cost"]

    fig = go.Figure()
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            name=row["city"],
            x=labels,
            y=[row[c] for c in components],
        ))

    fig.update_layout(
        barmode="group",
        height=350,
        margin=dict(t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        yaxis=dict(range=[0, 100], title="Score"),
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Overall Stress Comparison")
    fig2 = px.bar(
        df,
        x="city",
        y="score",
        color="label",
        color_discrete_map=LABEL_COLORS,
        text="score",
        height=350,
    )
    fig2.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig2.update_layout(
        margin=dict(t=20, b=20),
        yaxis=dict(range=[0, 110], title="Stress Score"),
        showlegend=True,
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("30-Day Stress Score Trends")

hist_df = get_all_historical_scores()

if hist_df.empty:
    st.warning("No historical data available.")
    st.stop()

hist_df["date_id"] = pd.to_datetime(hist_df["date_id"])
last_30 = hist_df[hist_df["date_id"] >= hist_df["date_id"].max() - pd.Timedelta(days=30)]

fig3 = px.line(
    last_30,
    x="date_id",
    y="score",
    color="city",
    height=400,
    labels={"date_id": "Date", "score": "Stress Score", "city": "City"},
)
fig3.update_layout(margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)

st.divider()
st.markdown(
    "Built with Python · SQLite · Streamlit · Plotly | "
    "Data: TomTom · OpenAQ · OpenWeather · Open-Meteo · Numbeo"
)