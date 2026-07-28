import streamlit as st

st.set_page_config(
    page_title="Insurance Analytics - Cortex AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: #e94560;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #a8dadc;
        font-size: 1.1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    .stMetric {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #0f3460;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>Insurance Analytics Platform</h1>
    <p>Powered by Snowflake Cortex AI | Real-time Underwriting & Claims Intelligence</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Navigate to a use case from the sidebar")
st.markdown("""
| Page | Use Case | AI Capability |
|------|----------|---------------|
| Executive Dashboard | KPI summaries with AI narratives | Cortex LLM (claude-3-5-sonnet) |
| Fraud Intelligence | Anomaly detection & risk assessment | ML Anomaly Detection + LLM |
| Claims Triage | Priority classification & recommendations | Cortex LLM |
| Underwriter Insights | Performance coaching & analytics | Cortex LLM |
| Forecasting | Predictive claims volume modeling | ML Forecast |
| Ask Me Anything | Natural language data querying | Cortex Analyst |
| Adjuster Workload | Workload optimization & rebalancing | Cortex LLM |
""")
