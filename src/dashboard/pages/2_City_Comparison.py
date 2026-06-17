import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.dashboard.utils.db import get_cities, get_latest_scores, get_historical_scores

st.set_page_config(page_title="City Comparison", page_icon="🏙️", layout="wide")
st.title("🏙️ City Comparison")

from src.dashboard.utils.styling import inject_css, chart_theme
inject_css()

cities   = get_cities()
selected = st.multiselect("Select cities to compare", cities, default=cities[:2])

if len(selected) < 2:
    st.warning("Please select at least 2 cities.")
    st.stop()

df_latest = get_latest_scores()
df_latest = df_latest[df_latest["city"].isin(selected)]

st.subheader("Component Score Radar Chart")
components  = ["traffic_score", "air_quality_score", "weather_score", "safety_score", "cost_score"]
comp_labels = ["Traffic", "Air Quality", "Weather", "Safety", "Cost"]

fig = go.Figure()
for _, row in df_latest.iterrows():
    values = [row[c] for c in components]
    values += [values[0]]
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=comp_labels + [comp_labels[0]],
        fill="toself",
        name=row["city"],
        opacity=0.7,
    ))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    height=450,
    margin=dict(t=40, b=40),
)
st.plotly_chart(chart_theme(fig), use_container_width=True)

st.subheader("Side-by-Side Component Scores")
col_pairs = st.columns(len(selected))
for i, city in enumerate(selected):
    city_row = df_latest[df_latest["city"] == city]
    if city_row.empty:
        continue
    row = city_row.iloc[0]
    with col_pairs[i]:
        st.markdown(f"### {city}")
        st.metric("Total Score",   f"{row['score']:.1f}")
        st.metric("Traffic",       f"{row['traffic_score']:.1f}")
        st.metric("Air Quality",   f"{row['air_quality_score']:.1f}")
        st.metric("Weather",       f"{row['weather_score']:.1f}")
        st.metric("Safety",        f"{row['safety_score']:.1f}")
        st.metric("Cost",          f"{row['cost_score']:.1f}")

st.subheader("Historical Score Comparison")
period = st.selectbox("Time period", ["30 days", "90 days", "180 days", "All time"])
days_map = {"30 days": 30, "90 days": 90, "180 days": 180, "All time": 99999}
days     = days_map[period]

all_hist = pd.concat([get_historical_scores(c) for c in selected])
if days < 99999:
    all_hist = all_hist[all_hist["date_id"] >= all_hist["date_id"].max() - pd.Timedelta(days=days)]

fig2 = px.line(
    all_hist,
    x="date_id",
    y="score",
    color="city",
    height=400,
    labels={"date_id": "Date", "score": "Stress Score"},
)
fig2.update_layout(margin=dict(t=20, b=20))
st.plotly_chart(chart_theme(fig2), use_container_width=True)