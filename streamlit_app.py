import streamlit as st

home        = st.Page("src/dashboard/app.py", title="Home", icon="🏠", default=True)
rankings    = st.Page("src/dashboard/pages/1_Rankings.py", title="Rankings", icon="🏆")
comparison  = st.Page("src/dashboard/pages/2_City_Comparison.py", title="City Comparison", icon="🏙️")
trends      = st.Page("src/dashboard/pages/3_Historical_Trends.py", title="Historical Trends", icon="📈")
forecasts   = st.Page("src/dashboard/pages/4_Forecasts.py", title="Forecasts", icon="🔮")
anomalies   = st.Page("src/dashboard/pages/5_Anomaly_Detection.py", title="Anomaly Detection", icon="🚨")
clusters    = st.Page("src/dashboard/pages/6_Cluster_Explorer.py", title="Cluster Explorer", icon="🗂️")
methodology = st.Page("src/dashboard/pages/7_Methodology.py", title="Methodology", icon="📋")

pg = st.navigation([home, rankings, comparison, trends, forecasts, anomalies, clusters, methodology])
pg.run()