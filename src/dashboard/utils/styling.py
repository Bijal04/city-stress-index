import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@500;600&display=swap');

    /* ── Base ─────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #080D1A;
        color: #CBD5E8;
    }

    /* ── Main app background ──────────────────────────────── */
    .stApp {
        background: radial-gradient(ellipse at 20% 0%, #0D1829 0%, #080D1A 60%);
    }

    /* ── Top header bar ───────────────────────────────────── */
    [data-testid="stHeader"] {
        background-color: rgba(8, 13, 26, 0.95);
        border-bottom: 1px solid rgba(99, 130, 201, 0.15);
        backdrop-filter: blur(12px);
    }

    /* ── Headings ─────────────────────────────────────────── */
    h1, h2, h3 {
        font-family: 'Syne', sans-serif !important;
        letter-spacing: -0.5px;
        color: #EEF2FF !important;
    }

    h1 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #EEF2FF 0%, #A5B8F3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    h1::after {
        content: '';
        display: block;
        width: 80px;
        height: 3px;
        margin-top: 12px;
        border-radius: 2px;
        background: linear-gradient(90deg, #E8A838, #F2C96A, transparent);
        animation: shimmer 3s ease-in-out infinite;
    }

    h2 {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #A5B8F3 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px !important;
    }

    @keyframes shimmer {
        0%, 100% { opacity: 0.3; width: 40px; }
        50%       { opacity: 1;   width: 80px; }
    }

    @media (prefers-reduced-motion: reduce) {
        h1::after { animation: none; opacity: 0.8; width: 80px; }
    }

    /* ── Sidebar ──────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1829 0%, #080D1A 100%);
        border-right: 1px solid rgba(99, 130, 201, 0.12);
    }
    [data-testid="stSidebar"] a {
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] a:hover {
        background-color: rgba(99, 130, 201, 0.1) !important;
        padding-left: 8px;
    }

    /* ── Metric cards ─────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0F1A2E 0%, #111827 100%);
        border: 1px solid rgba(99, 130, 201, 0.18);
        border-radius: 14px;
        padding: 20px 16px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }

    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #E8A838, transparent);
        opacity: 0;
        transition: opacity 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(232, 168, 56, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }

    [data-testid="stMetric"]:hover::before {
        opacity: 1;
    }

    [data-testid="stMetricLabel"] {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #6382C9 !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        font-size: 2rem !important;
        color: #EEF2FF !important;
    }

    [data-testid="stMetricDelta"] {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }

    /* ── Dividers ─────────────────────────────────────────── */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99, 130, 201, 0.25), transparent);
        margin: 28px 0;
    }

    /* ── Buttons ──────────────────────────────────────────── */
    .stButton > button {
        background-color: transparent;
        border: 1px solid rgba(232, 168, 56, 0.5);
        color: #E8A838;
        border-radius: 8px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #E8A838;
        color: #080D1A;
        border-color: #E8A838;
        box-shadow: 0 0 20px rgba(232, 168, 56, 0.3);
    }

    /* ── Caption / small text ─────────────────────────────── */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #4A5568 !important;
        font-size: 11px !important;
        letter-spacing: 0.5px;
    }

    /* ── Dataframes ───────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(99, 130, 201, 0.15);
        border-radius: 10px;
        overflow: hidden;
    }

    /* ── Warning / info boxes ─────────────────────────────── */
    [data-testid="stAlert"] {
        background-color: rgba(13, 24, 41, 0.8);
        border: 1px solid rgba(99, 130, 201, 0.2);
        border-radius: 10px;
    }

    /* ── Selectbox / inputs ───────────────────────────────── */
    [data-testid="stSelectbox"] > div > div {
        background-color: #0F1A2E;
        border: 1px solid rgba(99, 130, 201, 0.2);
        border-radius: 8px;
        color: #CBD5E8;
    }

    /* ── Scrollbar ────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #080D1A; }
    ::-webkit-scrollbar-thumb {
        background: rgba(99, 130, 201, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #E8A838; }

    /* ── Footer ───────────────────────────────────────────── */
    footer { visibility: hidden; }
    .footer-custom {
        text-align: center;
        color: #2D3748;
        font-size: 11px;
        letter-spacing: 0.8px;
        padding: 16px 0;
        font-family: 'JetBrains Mono', monospace;
    }
    </style>
    """, unsafe_allow_html=True)


def chart_theme(fig):
    """Apply premium dark navy styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8, 13, 26, 0.4)",
        font=dict(color="#CBD5E8", family="DM Sans, sans-serif", size=12),
        legend=dict(
            font=dict(color="#CBD5E8", size=11),
            bgcolor="rgba(13, 24, 41, 0.8)",
            bordercolor="rgba(99, 130, 201, 0.2)",
            borderwidth=1,
        ),
        xaxis=dict(
            gridcolor="rgba(99, 130, 201, 0.08)",
            zerolinecolor="rgba(99, 130, 201, 0.15)",
            color="#4A5568",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            gridcolor="rgba(99, 130, 201, 0.08)",
            zerolinecolor="rgba(99, 130, 201, 0.15)",
            color="#4A5568",
            tickfont=dict(size=11),
        ),
        hoverlabel=dict(
            bgcolor="#0F1A2E",
            bordercolor="rgba(99, 130, 201, 0.3)",
            font=dict(color="#EEF2FF", size=12),
        ),
    )
    return fig