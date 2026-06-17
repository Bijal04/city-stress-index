import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Top header bar */
    [data-testid="stHeader"] {
        background-color: #0E1320;
        border-bottom: 1px solid #2A3349;
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 0.3px;
    }

    h1::after {
        content: '';
        display: block;
        width: 64px;
        height: 3px;
        margin-top: 10px;
        border-radius: 2px;
        background: linear-gradient(90deg, #F2A93C, transparent);
        animation: pulse 2.5s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 1; }
    }

    @media (prefers-reduced-motion: reduce) {
        h1::after { animation: none; opacity: 0.8; }
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161D2E;
        border-right: 1px solid #2A3349;
    }
    [data-testid="stSidebar"] a {
        border-radius: 6px;
        transition: background-color 0.15s ease;
    }
    [data-testid="stSidebar"] a:hover {
        background-color: #1F2840 !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #161D2E;
        border: 1px solid #2A3349;
        border-radius: 10px;
        padding: 16px 12px;
        transition: border-color 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #F2A93C;
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600;
    }

    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, #2A3349, transparent);
        margin: 24px 0;
    }

    /* Buttons */
    .stButton > button {
        background-color: transparent;
        border: 1px solid #F2A93C;
        color: #F2A93C;
        border-radius: 8px;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background-color: #F2A93C;
        color: #0E1320;
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid #2A3349;
        border-radius: 8px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0E1320; }
    ::-webkit-scrollbar-thumb { background: #2A3349; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #F2A93C; }
    </style>
    """, unsafe_allow_html=True)


def chart_theme(fig):
    """Apply dark command-center styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#EDF0F7", family="Inter, sans-serif"),
        legend=dict(font=dict(color="#EDF0F7")),
        xaxis=dict(gridcolor="#2A3349", zerolinecolor="#2A3349", color="#8893AC"),
        yaxis=dict(gridcolor="#2A3349", zerolinecolor="#2A3349", color="#8893AC"),
    )
    return fig