import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Executive Dashboard", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .narrative-box {
        background: #f0f4f8;
        border-left: 5px solid #667eea;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("Executive Dashboard")
st.caption("Underwriting & Claims Performance Overview with AI-Generated Narratives")

# KPI summary via SQL
kpi_df = session.sql("""
    SELECT SUM(POLICY_COUNT) AS TOTAL_POLICIES,
           AVG(APPROVAL_RATE) AS AVG_APPROVAL_RATE,
           AVG(AVG_RISK_SCORE) AS AVG_RISK_SCORE,
           AVG(AVG_PREMIUM_AMOUNT) AS AVG_PREMIUM,
           AVG(AVG_COVERAGE_AMOUNT) AS AVG_COVERAGE
    FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_UNDERWRITING
""").to_pandas()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Policies", f"{kpi_df['TOTAL_POLICIES'].iloc[0]:,.0f}")
with col2:
    st.metric("Avg Approval Rate", f"{kpi_df['AVG_APPROVAL_RATE'].iloc[0]:.0f}%")
with col3:
    st.metric("Avg Risk Score", f"{kpi_df['AVG_RISK_SCORE'].iloc[0]:.1f}")
with col4:
    st.metric("Avg Premium", f"${kpi_df['AVG_PREMIUM'].iloc[0]:,.0f}")
with col5:
    st.metric("Avg Coverage", f"${kpi_df['AVG_COVERAGE'].iloc[0]:,.0f}")

st.divider()

# Trends section
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Monthly Policy Volume by Product")
    monthly_df = session.sql("""
        SELECT MONTH, PRODUCT_TYPE, SUM(POLICY_COUNT) AS POLICY_COUNT
        FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_UNDERWRITING
        GROUP BY MONTH, PRODUCT_TYPE
        ORDER BY MONTH, PRODUCT_TYPE
    """).to_pandas()
    fig1 = px.area(monthly_df, x='MONTH', y='POLICY_COUNT', color='PRODUCT_TYPE',
                   color_discrete_sequence=px.colors.qualitative.Set2,
                   template='plotly_white')
    fig1.update_layout(height=350, margin=dict(t=20, b=20))
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    st.subheader("Approval Rate Trend by Product")
    approval_df = session.sql("""
        SELECT MONTH, PRODUCT_TYPE, APPROVAL_RATE
        FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_UNDERWRITING
        ORDER BY MONTH, PRODUCT_TYPE
    """).to_pandas()
    fig2 = px.line(approval_df, x='MONTH', y='APPROVAL_RATE', color='PRODUCT_TYPE',
                   markers=True, color_discrete_sequence=px.colors.qualitative.Set2,
                   template='plotly_white')
    fig2.update_layout(height=350, margin=dict(t=20, b=20), yaxis_title="Approval Rate (%)")
    st.plotly_chart(fig2, use_container_width=True)

# Product comparison
st.subheader("Product Type Comparison")
product_agg = session.sql("""
    SELECT PRODUCT_TYPE, 
           SUM(POLICY_COUNT) AS POLICY_COUNT,
           AVG(APPROVAL_RATE) AS APPROVAL_RATE,
           AVG(AVG_RISK_SCORE) AS AVG_RISK_SCORE,
           AVG(AVG_PREMIUM_AMOUNT) AS AVG_PREMIUM_AMOUNT
    FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_UNDERWRITING
    GROUP BY PRODUCT_TYPE
    ORDER BY POLICY_COUNT DESC
""").to_pandas()

col1, col2 = st.columns(2)
with col1:
    fig3 = go.Figure(data=[
        go.Bar(x=product_agg['PRODUCT_TYPE'], y=product_agg['POLICY_COUNT'],
               marker_color=['#a1c9f4','#ffb482','#8de5a1','#ff9f9b','#d0bbff'])
    ])
    fig3.update_layout(height=300, template='plotly_white', title='Total Policies by Product',
                       xaxis_title='Product Type', yaxis_title='Policy Count')
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    fig4 = go.Figure(data=[
        go.Bar(name='Risk Score', x=product_agg['PRODUCT_TYPE'], y=product_agg['AVG_RISK_SCORE'], marker_color='#e94560'),
        go.Bar(name='Approval Rate', x=product_agg['PRODUCT_TYPE'], y=product_agg['APPROVAL_RATE'], marker_color='#667eea')
    ])
    fig4.update_layout(barmode='group', height=300, template='plotly_white', title='Risk Score vs Approval Rate')
    st.plotly_chart(fig4, use_container_width=True)

# AI Narrative
st.divider()
st.subheader("AI-Generated Executive Narrative")

product_list = session.sql("SELECT DISTINCT PRODUCT_TYPE FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_UNDERWRITING ORDER BY 1").to_pandas()
product_filter = st.selectbox("Select Product Type for AI Narrative", product_list['PRODUCT_TYPE'].tolist())

if st.button("Generate AI Narrative", type="primary"):
    latest_month = session.sql(f"""
        SELECT MONTH, POLICY_COUNT, APPROVAL_RATE, AVG_RISK_SCORE, AVG_PREMIUM_AMOUNT, AVG_COVERAGE_AMOUNT
        FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_UNDERWRITING
        WHERE PRODUCT_TYPE = '{product_filter}'
        ORDER BY MONTH DESC
        LIMIT 1
    """).to_pandas()
    row = latest_month.iloc[0]
    with st.spinner("Generating executive summary with Cortex AI..."):
        result = session.sql(f"""
            SELECT ALTERYX_INSURANCE_DB.PUBLIC.GENERATE_KPI_NARRATIVE(
                '{row['MONTH']}',
                '{product_filter}',
                {int(row['POLICY_COUNT'])},
                {int(row['APPROVAL_RATE'])},
                {row['AVG_RISK_SCORE']},
                {row['AVG_PREMIUM_AMOUNT']},
                {row['AVG_COVERAGE_AMOUNT']}
            ) AS NARRATIVE
        """).to_pandas()
        st.markdown(f"""<div class="narrative-box">{result['NARRATIVE'].iloc[0]}</div>""", unsafe_allow_html=True)
