import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Adjuster Workload", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .workload-box {
        background: linear-gradient(135deg, #fff8e1, #ffecb3);
        border-left: 5px solid #ff8f00;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .overloaded { background: #ffcdd2; border-left-color: #d32f2f; }
    .optimal { background: #c8e6c9; border-left-color: #388e3c; }
    .underutilized { background: #e1f5fe; border-left-color: #0277bd; }
</style>
""", unsafe_allow_html=True)

st.title("Adjuster Workload Optimizer")
st.caption("Regional Performance Analysis & AI-Driven Workload Rebalancing")

# Fetch adjuster data
adj_df = session.sql("""
    SELECT * FROM ALTERYX_INSURANCE_DB.PUBLIC.ADJUSTER_PERFORMANCE
    ORDER BY CLAIM_COUNT DESC
""").to_pandas()

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Adjusters", f"{adj_df.shape[0]}")
with col2:
    st.metric("Total Claims", f"{adj_df['CLAIM_COUNT'].sum():,.0f}")
with col3:
    st.metric("Avg Settlement Rate", f"{adj_df['SETTLEMENT_RATE'].mean():.0f}%")
with col4:
    st.metric("Avg Days to Report", f"{adj_df['AVG_DAYS_TO_REPORT'].mean():.1f}")

st.divider()

# Regional view
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Claims Distribution by Region")
    region_agg = session.sql("""
        SELECT REGION, SUM(CLAIM_COUNT) AS CLAIM_COUNT, AVG(SETTLEMENT_RATE) AS SETTLEMENT_RATE, SUM(TOTAL_PAID) AS TOTAL_PAID
        FROM ALTERYX_INSURANCE_DB.PUBLIC.ADJUSTER_PERFORMANCE
        GROUP BY REGION
        ORDER BY CLAIM_COUNT DESC
    """).to_pandas()
    
    fig = go.Figure(data=[
        go.Bar(x=region_agg['REGION'].tolist(), y=region_agg['CLAIM_COUNT'].tolist(),
               marker_color=['#a1c9f4','#ffb482','#8de5a1','#ff9f9b','#d0bbff','#debb9b'])
    ])
    fig.update_layout(height=350, template='plotly_white', margin=dict(t=20, b=20),
                      xaxis_title='Region', yaxis_title='Claim Count')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Settlement Rate by Region")
    fig2 = go.Figure(data=[
        go.Bar(x=region_agg['REGION'].tolist(), y=region_agg['SETTLEMENT_RATE'].tolist(),
               marker_color=['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854','#ffd92f'])
    ])
    fig2.update_layout(height=350, template='plotly_white', margin=dict(t=20, b=20),
                       xaxis_title='Region', yaxis_title='Settlement Rate (%)')
    st.plotly_chart(fig2, use_container_width=True)

# Workload bubble chart
st.subheader("Adjuster Workload Analysis")
regions = adj_df['REGION'].unique().tolist()
colors = ['#e58606','#5d69b1','#52bca3','#99c945','#cc61b0','#24796c']
fig3 = go.Figure()
for i, region in enumerate(regions):
    subset = adj_df[adj_df['REGION'] == region]
    fig3.add_trace(go.Scatter(
        x=subset['CLAIM_COUNT'].tolist(),
        y=subset['SETTLEMENT_RATE'].tolist(),
        mode='markers', name=region,
        marker=dict(size=14, color=colors[i % len(colors)], opacity=0.8),
        text=subset['ADJUSTER_ID'].astype(str).tolist(),
        hovertemplate='Adjuster %{text}<br>Claims: %{x}<br>Settlement: %{y}%<extra></extra>'
    ))
fig3.update_layout(height=400, template='plotly_white',
                   xaxis_title='Total Claims', yaxis_title='Settlement Rate (%)',
                   title='Adjuster Workload by Region')
st.plotly_chart(fig3, use_container_width=True)

# Detailed adjuster comparison
st.subheader("Adjuster Performance Comparison")
adj_display = adj_df[['ADJUSTER_ID', 'REGION', 'CLAIM_COUNT', 'OPEN', 'SETTLED', 
                       'HIGH_PRIORITY', 'SETTLEMENT_RATE', 'AVG_DAYS_TO_REPORT']].copy()
st.dataframe(adj_display, use_container_width=True)

# AI Workload Recommendation
st.divider()
st.subheader("AI Workload Optimization")

selected_adjuster = st.selectbox("Select Adjuster", adj_df['ADJUSTER_ID'].tolist(),
                                  format_func=lambda x: f"Adjuster {x} - {adj_df[adj_df['ADJUSTER_ID']==x]['REGION'].values[0]}")

if st.button("Generate Workload Analysis", type="primary"):
    adj = adj_df[adj_df['ADJUSTER_ID'] == selected_adjuster].iloc[0]
    with st.spinner("Analyzing workload with Cortex AI..."):
        result = session.sql(f"""
            SELECT ALTERYX_INSURANCE_DB.PUBLIC.ADJUSTER_WORKLOAD_ANALYSIS(
                {int(adj['ADJUSTER_ID'])}, '{adj['REGION']}',
                {int(adj['CLAIM_COUNT'])}, {int(adj['OPEN'])},
                {int(adj['SETTLED'])}, {int(adj['HIGH_PRIORITY'])},
                {int(adj['SETTLEMENT_RATE'])}, {adj['AVG_DAYS_TO_REPORT']},
                {adj['AVG_PAYOUT_PCT']}
            ) AS ANALYSIS
        """).to_pandas()
        st.markdown(f"""<div class="workload-box">{result['ANALYSIS'].iloc[0]}</div>""", unsafe_allow_html=True)
