import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Fraud Intelligence", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .fraud-alert {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        border-radius: 10px;
        padding: 1.2rem;
        color: white;
        margin: 0.5rem 0;
    }
    .anomaly-card {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("Fraud Intelligence Center")
st.caption("AI-Powered Fraud Detection, Anomaly Analysis & Risk Assessment")

# Fetch fraud data
fraud_df = session.sql("""
    SELECT * FROM ALTERYX_INSURANCE_DB.PUBLIC.FRAUD_SUMMARY ORDER BY MONTH
""").to_pandas()

# Claims with fraud flag
claims_fraud = session.sql("""
    SELECT MONTH, PRODUCT_TYPE, CLAIM_TYPE, SUM(FRAUD) as FRAUD_COUNT, 
           SUM(ESTIMATED_AMOUNT) as TOTAL_ESTIMATED
    FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS
    WHERE FRAUD > 0
    GROUP BY MONTH, PRODUCT_TYPE, CLAIM_TYPE
    ORDER BY MONTH
""").to_pandas()

# Anomaly results
anomaly_df = session.sql("""
    SELECT * FROM ALTERYX_INSURANCE_DB.PUBLIC.FRAUD_ANOMALY_RESULTS
    ORDER BY TS
""").to_pandas()

# KPI row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Fraud Claims", f"{fraud_df['CLAIM_COUNT'].sum():,.0f}")
with col2:
    st.metric("Total Fraud Paid", f"${fraud_df['TOTAL_PAID'].sum():,.0f}")
with col3:
    anomalies_found = anomaly_df[anomaly_df['IS_ANOMALY'] == True].shape[0] if 'IS_ANOMALY' in anomaly_df.columns else 0
    st.metric("Anomalies Detected", f"{anomalies_found}")
with col4:
    st.metric("Open Fraud Cases", f"{fraud_df['IS_OPEN'].sum():,.0f}")

st.divider()

# Fraud heatmap
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Fraud Heatmap: Product x Claim Type")
    heatmap_data = session.sql("""
        SELECT PRODUCT_TYPE, CLAIM_TYPE, SUM(CLAIM_COUNT) AS CLAIM_COUNT
        FROM ALTERYX_INSURANCE_DB.PUBLIC.FRAUD_SUMMARY
        GROUP BY PRODUCT_TYPE, CLAIM_TYPE
        ORDER BY PRODUCT_TYPE, CLAIM_TYPE
    """).to_pandas()
    fig = go.Figure()
    for product in heatmap_data['PRODUCT_TYPE'].unique():
        subset = heatmap_data[heatmap_data['PRODUCT_TYPE'] == product]
        fig.add_trace(go.Bar(name=product, x=subset['CLAIM_TYPE'], y=subset['CLAIM_COUNT']))
    fig.update_layout(barmode='group', height=350, template='plotly_white',
                      margin=dict(t=20, b=20), xaxis_title='Claim Type', yaxis_title='Fraud Claims')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Fraud Claims Over Time")
    fraud_time = session.sql("""
        SELECT MONTH, PRODUCT_TYPE, SUM(CLAIM_COUNT) AS CLAIM_COUNT
        FROM ALTERYX_INSURANCE_DB.PUBLIC.FRAUD_SUMMARY
        GROUP BY MONTH, PRODUCT_TYPE
        ORDER BY MONTH
    """).to_pandas()
    fig2 = px.line(fraud_time, x='MONTH', y='CLAIM_COUNT', color='PRODUCT_TYPE',
                   markers=True, color_discrete_sequence=px.colors.qualitative.Bold,
                   template='plotly_white')
    fig2.update_layout(height=350, margin=dict(t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)

# Anomaly detection visualization
st.subheader("Anomaly Detection Results")
if not anomaly_df.empty:
    series_filter = st.selectbox("Select Product Type", anomaly_df['SERIES'].unique(), key='anomaly_series')
    filtered_anomaly = anomaly_df[anomaly_df['SERIES'] == series_filter].copy()
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=filtered_anomaly['TS'], y=filtered_anomaly['Y'],
                              mode='lines+markers', name='Actual', line=dict(color='#667eea', width=2)))
    fig3.add_trace(go.Scatter(x=filtered_anomaly['TS'], y=filtered_anomaly['FORECAST'],
                              mode='lines', name='Expected', line=dict(color='#a8dadc', dash='dash')))
    fig3.add_trace(go.Scatter(x=filtered_anomaly['TS'], y=filtered_anomaly['UPPER_BOUND'],
                              mode='lines', name='Upper Bound', line=dict(color='rgba(233,69,96,0.3)'), showlegend=False))
    fig3.add_trace(go.Scatter(x=filtered_anomaly['TS'], y=filtered_anomaly['LOWER_BOUND'],
                              mode='lines', name='Lower Bound', fill='tonexty',
                              line=dict(color='rgba(233,69,96,0.3)'), fillcolor='rgba(233,69,96,0.1)', showlegend=False))
    
    if 'IS_ANOMALY' in filtered_anomaly.columns:
        anomalies = filtered_anomaly[filtered_anomaly['IS_ANOMALY'] == True]
        if not anomalies.empty:
            fig3.add_trace(go.Scatter(x=anomalies['TS'], y=anomalies['Y'],
                                     mode='markers', name='ANOMALY',
                                     marker=dict(color='red', size=14, symbol='x')))
    
    fig3.update_layout(height=350, template='plotly_white', title=f'Anomaly Detection - {series_filter}')
    st.plotly_chart(fig3, use_container_width=True)

# AI Fraud Risk Assessment
st.divider()
st.subheader("AI Fraud Risk Assessment")

col_a, col_b = st.columns(2)
with col_a:
    fraud_product = st.selectbox("Product Type", fraud_df['PRODUCT_TYPE'].unique(), key='fraud_prod')
with col_b:
    fraud_claim = st.selectbox("Claim Type", fraud_df['CLAIM_TYPE'].unique(), key='fraud_claim')

if st.button("Generate Fraud Risk Assessment", type="primary"):
    filtered = fraud_df[(fraud_df['PRODUCT_TYPE'] == fraud_product) & (fraud_df['CLAIM_TYPE'] == fraud_claim)]
    if not filtered.empty:
        row = filtered.iloc[0]
        with st.spinner("Analyzing fraud risk with Cortex AI..."):
            result = session.sql(f"""
                SELECT ALTERYX_INSURANCE_DB.PUBLIC.FRAUD_RISK_ASSESSMENT(
                    '{fraud_product}', '{fraud_claim}',
                    {int(row['CLAIM_COUNT'])}, {row['TOTAL_PAID']},
                    {row['ESTIMATED_AMOUNT']}, {int(row['IS_OPEN'])}, {int(row['IS_DECLINED'])}
                ) AS ASSESSMENT
            """).to_pandas()
            st.markdown(f"""<div class="anomaly-card">{result['ASSESSMENT'].iloc[0]}</div>""", unsafe_allow_html=True)
    else:
        st.warning("No fraud data available for this combination.")
