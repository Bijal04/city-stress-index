import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os
import json

sys.path.append(os.path.dirname(__file__))
from src.dashboard.utils.db import get_latest_scores, get_all_historical_scores

st.set_page_config(
    page_title="City Stress Index",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.dashboard.utils.styling import inject_css, chart_theme
inject_css()

LABEL_COLORS = {
    "Low":      "#2ecc71",
    "Moderate": "#f39c12",
    "High":     "#e67e22",
    "Critical": "#e74c3c",
}

# ── Load data ──────────────────────────────────────────────────
df = get_latest_scores()

if df.empty:
    st.warning("No data available. Run the pipeline first.")
    st.stop()

latest_date = df["date_id"].iloc[0]
num_cities  = len(df)

# ── Animated hero header ───────────────────────────────────────
st.components.v1.html(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@500&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  .hero {{
    position: relative;
    width: 100%;
    padding: 48px 0 36px;
    overflow: hidden;
    background: transparent;
  }}

  canvas#particles {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    opacity: 0.5;
  }}

  .hero-content {{
    position: relative;
    z-index: 2;
  }}

  .hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(232, 168, 56, 0.12);
    border: 1px solid rgba(232, 168, 56, 0.3);
    border-radius: 20px;
    padding: 4px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #E8A838;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 20px;
    animation: fadeSlideDown 0.6s ease both;
  }}

  .hero-badge .dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #2ecc71;
    animation: blink 1.5s ease-in-out infinite;
  }}

  @keyframes blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.2; }}
  }}

  .hero-title {{
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    color: #EEF2FF;
    line-height: 1.1;
    margin-bottom: 16px;
    animation: fadeSlideDown 0.7s ease 0.1s both;
  }}

  .hero-title span {{
    background: linear-gradient(135deg, #E8A838 0%, #F2C96A 50%, #E8A838 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmerText 3s linear infinite;
  }}

  @keyframes shimmerText {{
    0% {{ background-position: 0% center; }}
    100% {{ background-position: 200% center; }}
  }}

  .hero-sub {{
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: #6B7A99;
    max-width: 560px;
    line-height: 1.7;
    animation: fadeSlideDown 0.7s ease 0.2s both;
  }}

  .hero-stats {{
    display: flex;
    gap: 32px;
    margin-top: 32px;
    animation: fadeSlideDown 0.7s ease 0.3s both;
  }}

  .hero-stat {{
    display: flex;
    flex-direction: column;
    gap: 2px;
  }}

  .hero-stat-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 500;
    color: #EEF2FF;
  }}

  .hero-stat-label {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    color: #4A5568;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}

  .hero-divider {{
    width: 1px;
    height: 40px;
    background: rgba(99, 130, 201, 0.2);
    align-self: center;
  }}

  @keyframes fadeSlideDown {{
    from {{ opacity: 0; transform: translateY(-16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
</style>

<div class="hero">
  <canvas id="particles"></canvas>
  <div class="hero-content">
    <div class="hero-badge">
      <div class="dot"></div>
      Live · Real-time Urban Intelligence
    </div>
    <h1 class="hero-title">🏙️ City Stress <span>Index</span></h1>
    <p class="hero-sub">
      A real-time urban health intelligence platform scoring city stress
      across traffic, air quality, weather, safety, and cost of living.
    </p>
    <div class="hero-stats">
      <div class="hero-stat">
        <span class="hero-stat-value" id="city-count">{num_cities}</span>
        <span class="hero-stat-label">Cities Tracked</span>
      </div>
      <div class="hero-divider"></div>
      <div class="hero-stat">
        <span class="hero-stat-value">5</span>
        <span class="hero-stat-label">Stress Factors</span>
      </div>
      <div class="hero-divider"></div>
      <div class="hero-stat">
        <span class="hero-stat-value" id="update-time">—</span>
        <span class="hero-stat-label">Last Updated</span>
      </div>
    </div>
  </div>
</div>

<script>
  // Particle background
  const canvas = document.getElementById('particles');
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;

  const particles = Array.from({{ length: 40 }}, () => ({{
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 1.5 + 0.5,
    dx: (Math.random() - 0.5) * 0.3,
    dy: (Math.random() - 0.5) * 0.3,
    alpha: Math.random() * 0.4 + 0.1,
  }}));

  function animateParticles() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {{
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > canvas.width)  p.dx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(99, 130, 201, ${{p.alpha}})`;
      ctx.fill();
    }});
    requestAnimationFrame(animateParticles);
  }}
  animateParticles();

  // Set live time
  document.getElementById('update-time').textContent =
    new Date().toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit' }});
</script>
""", height=280)

# ── Animated city cards ────────────────────────────────────────
st.markdown("### Today's City Stress Rankings")

cities_json = df[["city", "score", "label",
                   "traffic_score", "air_quality_score",
                   "weather_score", "safety_score", "cost_score"]].to_dict(orient="records")

st.components.v1.html(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700&family=DM+Sans:wght@400;500&family=JetBrains+Mono:wght@600&display=swap');

  .cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px;
    padding: 4px 0 16px;
  }}

  .city-card {{
    background: linear-gradient(145deg, #0F1A2E, #0D1525);
    border: 1px solid rgba(99, 130, 201, 0.15);
    border-radius: 16px;
    padding: 20px 16px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
    opacity: 0;
    transform: translateY(20px);
  }}

  .city-card.visible {{
    opacity: 1;
    transform: translateY(0);
  }}

  .city-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
    transition: opacity 0.3s ease;
    opacity: 0.6;
  }}

  .city-card:hover {{
    transform: translateY(-6px) scale(1.02);
    border-color: rgba(232, 168, 56, 0.35);
    box-shadow: 0 16px 40px rgba(0,0,0,0.4);
  }}

  .city-card:hover::before {{ opacity: 1; }}

  .card-city {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #4A5568;
    margin-bottom: 10px;
  }}

  .card-score {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.4rem;
    font-weight: 600;
    color: #EEF2FF;
    line-height: 1;
    margin-bottom: 8px;
  }}

  .card-label {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 14px;
  }}

  .card-label .dot {{
    width: 5px; height: 5px;
    border-radius: 50%;
  }}

  .mini-bars {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 4px;
  }}

  .mini-bar-row {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .mini-bar-label {{
    font-family: 'DM Sans', sans-serif;
    font-size: 9px;
    color: #3A4560;
    width: 22px;
    flex-shrink: 0;
  }}

  .mini-bar-track {{
    flex: 1;
    height: 3px;
    background: rgba(99, 130, 201, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }}

  .mini-bar-fill {{
    height: 100%;
    border-radius: 2px;
    width: 0%;
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  }}

  .mini-bar-val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #3A4560;
    width: 20px;
    text-align: right;
  }}
</style>

<div class="cards-grid" id="cards-grid"></div>

<script>
const cities = {json.dumps(cities_json)};

const LABEL_STYLES = {{
  "Low":      {{ bg: "rgba(46,204,113,0.12)", color: "#2ecc71", bar: "#2ecc71", top: "#2ecc71" }},
  "Moderate": {{ bg: "rgba(243,156,18,0.12)",  color: "#f39c12", bar: "#f39c12", top: "#f39c12" }},
  "High":     {{ bg: "rgba(230,126,34,0.12)",  color: "#e67e22", bar: "#e67e22", top: "#e67e22" }},
  "Critical": {{ bg: "rgba(231,76,60,0.12)",   color: "#e74c3c", bar: "#e74c3c", top: "#e74c3c" }},
}};

const MINI_LABELS = ["Trf","Air","Wth","Saf","Cst"];
const MINI_KEYS   = ["traffic_score","air_quality_score","weather_score","safety_score","cost_score"];

const grid = document.getElementById('cards-grid');

cities.forEach((city, i) => {{
  const s  = LABEL_STYLES[city.label] || {{ bg:"rgba(99,130,201,0.1)", color:"#6382C9", bar:"#6382C9", top:"#6382C9" }};
  const el = document.createElement('div');
  el.className = 'city-card';
  el.style.setProperty('--card-top', s.top);
  el.style.cssText += `--card-top: ${{s.top}};`;
  el.querySelector = undefined;

  const miniBars = MINI_KEYS.map((k, j) => `
    <div class="mini-bar-row">
      <span class="mini-bar-label">${{MINI_LABELS[j]}}</span>
      <div class="mini-bar-track">
        <div class="mini-bar-fill" data-val="${{city[k]}}"
             style="background: ${{s.bar}}; opacity: 0.7;"></div>
      </div>
      <span class="mini-bar-val">${{Math.round(city[k])}}</span>
    </div>
  `).join('');

  el.innerHTML = `
    <style>
      .city-card:nth-child(${{i+1}})::before {{
        background: linear-gradient(90deg, ${{s.top}}, transparent);
      }}
    </style>
    <div class="card-city">${{city.city}}</div>
    <div class="card-score">${{city.score.toFixed(1)}}</div>
    <div class="card-label" style="background:${{s.bg}}; color:${{s.color}}">
      <div class="dot" style="background:${{s.color}}"></div>
      ${{city.label}}
    </div>
    <div class="mini-bars">${{miniBars}}</div>
  `;

  grid.appendChild(el);

  // Stagger entrance
  setTimeout(() => {{
    el.classList.add('visible');
    el.style.transition = `opacity 0.5s ease ${{i * 0.08}}s, transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) ${{i * 0.08}}s, border-color 0.3s ease, box-shadow 0.3s ease`;
    // Animate mini bars
    setTimeout(() => {{
      el.querySelectorAll('.mini-bar-fill').forEach(bar => {{
        bar.style.width = bar.dataset.val + '%';
      }});
    }}, 300 + i * 80);
  }}, 50);
}});
</script>
""", height=320)

st.divider()

# ── Charts ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Stress Score Breakdown")
    components = ["traffic_score","air_quality_score","weather_score","safety_score","cost_score"]
    labels     = ["Traffic","Air Quality","Weather","Safety","Cost"]

    fig = go.Figure()
    CITY_COLORS = ["#6382C9","#E8A838","#2ecc71","#e74c3c","#9b59b6","#1abc9c"]
    for idx, (_, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Bar(
            name=row["city"],
            x=labels,
            y=[row[c] for c in components],
            marker_color=CITY_COLORS[idx % len(CITY_COLORS)],
            marker_line_width=0,
        ))

    fig.update_layout(
        barmode="group",
        height=360,
        margin=dict(t=10, b=20, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        yaxis=dict(range=[0, 100], title="Score", gridcolor="rgba(99,130,201,0.08)"),
        bargap=0.2,
        bargroupgap=0.05,
    )
    st.plotly_chart(chart_theme(fig), use_container_width=True)

with col2:
    st.markdown("### Overall Stress Comparison")
    fig2 = px.bar(
        df,
        x="city",
        y="score",
        color="label",
        color_discrete_map=LABEL_COLORS,
        text="score",
        height=360,
    )
    fig2.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        marker_line_width=0,
    )
    fig2.update_layout(
        margin=dict(t=10, b=20, l=0, r=0),
        yaxis=dict(range=[0, 110], title="Stress Score"),
        showlegend=True,
        bargap=0.3,
    )
    st.plotly_chart(chart_theme(fig2), use_container_width=True)

st.divider()

# ── Trend chart ────────────────────────────────────────────────
st.markdown("### 30-Day Stress Score Trends")

hist_df = get_all_historical_scores()
last_30  = hist_df[hist_df["date_id"] >= hist_df["date_id"].max() - pd.Timedelta(days=30)]

fig3 = px.line(
    last_30,
    x="date_id",
    y="score",
    color="city",
    height=420,
    labels={"date_id": "Date", "score": "Stress Score", "city": "City"},
    color_discrete_sequence=["#6382C9","#E8A838","#2ecc71","#e74c3c","#9b59b6","#1abc9c"],
)
fig3.update_traces(line=dict(width=2.5))
fig3.update_layout(
    margin=dict(t=10, b=20, l=0, r=0),
    hovermode="x unified",
)
st.plotly_chart(chart_theme(fig3), use_container_width=True)

st.divider()

# ── Animated footer ────────────────────────────────────────────
st.components.v1.html("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&display=swap');
  .footer {
    text-align: center;
    padding: 16px 0 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #2D3748;
    letter-spacing: 0.8px;
    animation: fadeIn 1s ease 0.5s both;
  }
  .footer span { color: #3A4560; }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
<div class="footer">
  Built with <span>Python · SQLite · Streamlit · Plotly</span> &nbsp;|&nbsp;
  Data: <span>TomTom · OpenAQ · OpenWeather · Open-Meteo · Numbeo</span>
</div>
""", height=50)