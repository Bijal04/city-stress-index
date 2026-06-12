import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.dashboard.utils.db import get_cities, get_historical_scores, get_forecasts

st.set_page_config(page_title="Forecasts", page_icon="🔮", layout="wide")
st.title("🔮 Stress Score Forecasts")

cities = get_cities()
city   = st.selectbox("Select city", cities)
model  = st.radio("Forecast model", ["ARIMA", "Prophet", "Both"], horizontal=True)

hist_df = get_historical_scores(city)
last_90 = hist_df[hist_df["date_id"] >= hist_df["date_id"].max() - pd.Timedelta(days=90)]

fc_df = get_forecasts(city)
if model != "Both":
    fc_df = fc_df[fc_df["model"] == model]

st.subheader(f"30-Day Forecast — {city}")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=last_90["date_id"],
    y=last_90["score"],
    name="Historical",
    line=dict(color="#378ADD", width=2),
))

colors = {"ARIMA": "#E24B4A", "Prophet": "#1D9E75"}
for model_name, group in fc_df.groupby("model"):
    color = colors.get(model_name, "#888")
    fig.add_trace(go.Scatter(
        x=group["forecast_date"],
        y=group["predicted_score"],
        name=f"{model_name} Forecast",
        line=dict(color=color, width=2, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([group["forecast_date"], group["forecast_date"].iloc[::-1]]),
        y=pd.concat([group["upper_bound"], group["lower_bound"].iloc[::-1]]),
        fill="toself",
        fillcolor=color.replace(")", ", 0.1)").replace("rgb", "rgba") if "rgb" in color else color + "20",
        line=dict(color="rgba(255,255,255,0)"),
        name=f"{model_name} confidence",
        showlegend=False,
    ))

fig.update_layout(
    height=450,
    margin=dict(t=20, b=20),
    yaxis=dict(range=[0, 100], title="Stress Score"),
    xaxis=dict(title="Date"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Forecast Values Table")
if not fc_df.empty:
    display = fc_df[["forecast_date", "model", "predicted_score", "lower_bound", "upper_bound"]].copy()
    display["forecast_date"]   = display["forecast_date"].dt.strftime("%Y-%m-%d")
    display["predicted_score"] = display["predicted_score"].round(1)
    display["lower_bound"]     = display["lower_bound"].round(1)
    display["upper_bound"]     = display["upper_bound"].round(1)
    display.columns            = ["Date", "Model", "Predicted", "Lower Bound", "Upper Bound"]
    st.dataframe(display, use_container_width=True, hide_index=True)

st.subheader("All Cities — 7-Day Forecast Summary")
summary_rows = []
for c in cities:
    c_fc = get_forecasts(c)
    c_fc = c_fc[c_fc["model"] == "Prophet"] if not c_fc.empty else c_fc
    if not c_fc.empty:
        next7 = c_fc.head(7)["predicted_score"].mean()
        summary_rows.append({"City": c, "Avg Predicted Score (7d)": round(next7, 1)})

if summary_rows:
    summary_df = pd.DataFrame(summary_rows).sort_values("Avg Predicted Score (7d)", ascending=False)
    fig2 = px.bar(
        summary_df,
        x="City",
        y="Avg Predicted Score (7d)",
        height=350,
        color="Avg Predicted Score (7d)",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        range_color=[0, 100],
    )
    fig2.update_layout(margin=dict(t=20, b=20), coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)