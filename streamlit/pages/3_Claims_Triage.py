import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Claims Triage", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .triage-p1 { background: #dc3545; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .triage-p2 { background: #fd7e14; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .triage-p3 { background: #ffc107; color: #333; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .triage-p4 { background: #28a745; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .recommendation-box {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-left: 5px solid #0f3460;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("Claims Triage Command Center")
st.caption("AI-Assisted Claims Prioritization & Resource Allocation")

# Fetch claims data
claims_df = session.sql("""
    SELECT MONTH, CLAIM_TYPE, PRODUCT_TYPE, ESTIMATED_AMOUNT, APPROVED_AMOUNT,
           AVG_DAYS_TO_REPORT, AVG_PAYOUT_RATIO, HIGH_PRIORITY, FRAUD, SETTLED, CLOSED
    FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS
    ORDER BY MONTH DESC
""").to_pandas()

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("High Priority Claims", f"{claims_df['HIGH_PRIORITY'].sum():,.0f}")
with col2:
    st.metric("Fraud Flagged", f"{claims_df['FRAUD'].sum():,.0f}")
with col3:
    st.metric("Avg Days to Report", f"{claims_df['AVG_DAYS_TO_REPORT'].mean():.1f}")
with col4:
    st.metric("Total Estimated", f"${claims_df['ESTIMATED_AMOUNT'].sum():,.0f}")

st.divider()

# Priority matrix
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Priority Matrix: Severity vs Days to Report")
    scatter_data = session.sql("""
        SELECT CLAIM_TYPE, PRODUCT_TYPE,
               AVG(ESTIMATED_AMOUNT) AS ESTIMATED_AMOUNT,
               AVG(AVG_DAYS_TO_REPORT) AS AVG_DAYS_TO_REPORT,
               SUM(HIGH_PRIORITY) AS HIGH_PRIORITY,
               SUM(FRAUD) AS FRAUD
        FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS
        GROUP BY CLAIM_TYPE, PRODUCT_TYPE
    """).to_pandas()
    
    colors = ['#e58606','#5d69b1','#52bca3','#99c945','#cc61b0','#24796c','#daa51b']
    claim_types = scatter_data['CLAIM_TYPE'].unique().tolist()
    fig = go.Figure()
    for i, ct in enumerate(claim_types):
        subset = scatter_data[scatter_data['CLAIM_TYPE'] == ct]
        fig.add_trace(go.Scatter(
            x=subset['AVG_DAYS_TO_REPORT'].tolist(),
            y=subset['ESTIMATED_AMOUNT'].tolist(),
            mode='markers', name=ct,
            marker=dict(size=14, color=colors[i % len(colors)], opacity=0.8),
            text=subset['PRODUCT_TYPE'].tolist(),
            hovertemplate='%{text}<br>Days: %{x:.1f}<br>Amount: $%{y:,.0f}<extra></extra>'
        ))
    fig.update_layout(height=400, template='plotly_white', margin=dict(t=20, b=20),
                      xaxis_title='Avg Days to Report', yaxis_title='Avg Estimated Amount ($)')
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Claims Distribution by Type")
    type_agg = session.sql("""
        SELECT CLAIM_TYPE, SUM(ESTIMATED_AMOUNT) AS ESTIMATED_AMOUNT, SUM(HIGH_PRIORITY) AS HIGH_PRIORITY
        FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS
        GROUP BY CLAIM_TYPE
    """).to_pandas()
    
    fig2 = px.pie(type_agg, values='ESTIMATED_AMOUNT', names='CLAIM_TYPE',
                  color_discrete_sequence=px.colors.qualitative.Pastel,
                  template='plotly_white', hole=0.4)
    fig2.update_layout(height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)

# High priority trends
st.subheader("High Priority Claims Trend")
priority_trend = session.sql("""
    SELECT MONTH, PRODUCT_TYPE, SUM(HIGH_PRIORITY) AS HIGH_PRIORITY
    FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS
    GROUP BY MONTH, PRODUCT_TYPE
    ORDER BY MONTH
""").to_pandas()
fig3 = px.bar(priority_trend, x='MONTH', y='HIGH_PRIORITY', color='PRODUCT_TYPE',
              color_discrete_sequence=px.colors.qualitative.Set2, template='plotly_white',
              barmode='stack')
fig3.update_layout(height=300, margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)

# AI Triage Recommendation
st.divider()
st.subheader("AI Triage Recommendation")

col_a, col_b = st.columns(2)
with col_a:
    claim_types = session.sql("SELECT DISTINCT CLAIM_TYPE FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS ORDER BY 1").to_pandas()
    triage_claim_type = st.selectbox("Claim Type", claim_types['CLAIM_TYPE'].tolist())
with col_b:
    product_types = session.sql("SELECT DISTINCT PRODUCT_TYPE FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS ORDER BY 1").to_pandas()
    triage_product = st.selectbox("Product Type", product_types['PRODUCT_TYPE'].tolist())

if st.button("Generate Triage Recommendation", type="primary"):
    agg = session.sql(f"""
        SELECT SUM(HIGH_PRIORITY) AS HIGH_PRIORITY, SUM(FRAUD) AS FRAUD,
               AVG(AVG_DAYS_TO_REPORT) AS AVG_DAYS_TO_REPORT, AVG(AVG_PAYOUT_RATIO) AS AVG_PAYOUT_RATIO,
               SUM(ESTIMATED_AMOUNT) AS ESTIMATED_AMOUNT, SUM(APPROVED_AMOUNT) AS APPROVED_AMOUNT
        FROM ALTERYX_INSURANCE_DB.PUBLIC.KPI_CLAIMS
        WHERE CLAIM_TYPE = '{triage_claim_type}' AND PRODUCT_TYPE = '{triage_product}'
    """).to_pandas()
    if agg['HIGH_PRIORITY'].iloc[0] is not None:
        row = agg.iloc[0]
        with st.spinner("Generating triage recommendation with Cortex AI..."):
            result = session.sql(f"""
                SELECT ALTERYX_INSURANCE_DB.PUBLIC.CLAIMS_TRIAGE_RECOMMENDATION(
                    '{triage_claim_type}', '{triage_product}',
                    {int(row['HIGH_PRIORITY'])}, {int(row['FRAUD'])},
                    {row['AVG_DAYS_TO_REPORT']:.1f}, {row['AVG_PAYOUT_RATIO']:.1f},
                    {row['ESTIMATED_AMOUNT']:.2f}, {row['APPROVED_AMOUNT']:.2f}
                ) AS RECOMMENDATION
            """).to_pandas()
            st.markdown(f"""<div class="recommendation-box">{result['RECOMMENDATION'].iloc[0]}</div>""", unsafe_allow_html=True)
    else:
        st.warning("No claims data available for this combination.")
