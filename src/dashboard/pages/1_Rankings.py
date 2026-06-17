import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.dashboard.utils.db import get_rankings_history, get_latest_scores

st.set_page_config(page_title="Rankings", page_icon="🏆", layout="wide")
st.title("🏆 City Stress Rankings")

from src.dashboard.utils.styling import inject_css, chart_theme
inject_css()

LABEL_COLORS = {
    "Low": "#2ecc71", "Moderate": "#f39c12",
    "High": "#e67e22", "Critical": "#e74c3c",
}

df_latest = get_latest_scores()
df_hist   = get_rankings_history()

st.subheader("Current Rankings")
for i, (_, row) in enumerate(df_latest.iterrows()):
    col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
    with col1:
        st.markdown(f"### #{i+1}")
    with col2:
        st.markdown(f"**{row['city']}**")
    with col3:
        st.metric("Score", f"{row['score']:.1f}")
    with col4:
        color = LABEL_COLORS.get(row["label"], "#888")
        st.markdown(
            f"<div style='padding:6px 12px; background:{color}20; color:{color}; "
            f"border-radius:8px; font-weight:500; text-align:center'>{row['label']}</div>",
            unsafe_allow_html=True,
        )
    st.divider()

st.subheader("Ranking History (last 90 days)")
if not df_hist.empty:
    last_90 = df_hist[df_hist["date_id"] >= df_hist["date_id"].max() - pd.Timedelta(days=90)]
    fig = px.line(
        last_90,
        x="date_id",
        y="rank",
        color="city",
        height=400,
        labels={"date_id": "Date", "rank": "Rank (1 = most stressed)", "city": "City"},
    )
    fig.update_yaxes(autorange="reversed", tickvals=[1, 2, 3, 4, 5])
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(chart_theme(fig), use_container_width=True)

st.subheader("Score Distribution by City")
if not df_hist.empty:
    fig2 = px.box(
        df_hist,
        x="city",
        y="score",
        color="city",
        height=400,
        labels={"score": "Stress Score", "city": "City"},
    )
    fig2.update_layout(showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(chart_theme(fig2), use_container_width=True)