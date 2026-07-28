import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Forecasting", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .forecast-insight {
        background: linear-gradient(135deg, #e8f5e9, #c8e6c9);
        border-left: 5px solid #2e7d32;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("Predictive Claims Forecasting")
st.caption("ML-Powered Claims Volume Prediction with Confidence Intervals")

# Fetch actual data
actuals_df = session.sql("""
    SELECT TS as MONTH, SERIES as PRODUCT_TYPE, TOTAL_ESTIMATED_AMOUNT
    FROM ALTERYX_INSURANCE_DB.PUBLIC.CLAIMS_FORECAST_TRAINING
    ORDER BY TS
""").to_pandas()

# Fetch forecast data
forecast_df = session.sql("""
    SELECT TS as MONTH, SERIES as PRODUCT_TYPE, FORECAST, LOWER_BOUND, UPPER_BOUND
    FROM ALTERYX_INSURANCE_DB.PUBLIC.CLAIMS_FORECAST_RESULTS
    ORDER BY TS
""").to_pandas()

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Forecast Periods", "6 months")
with col2:
    avg_forecast = forecast_df['FORECAST'].mean()
    st.metric("Avg Forecasted Amount", f"${avg_forecast:,.0f}")
with col3:
    st.metric("Products Forecasted", f"{forecast_df['PRODUCT_TYPE'].nunique()}")
with col4:
    st.metric("Confidence Level", "95%")

st.divider()

# Product filter
product_filter = st.selectbox("Select Product Type", sorted(actuals_df['PRODUCT_TYPE'].unique()))

# Filter data
actuals_filtered = actuals_df[actuals_df['PRODUCT_TYPE'] == product_filter].copy()
forecast_filtered = forecast_df[forecast_df['PRODUCT_TYPE'] == product_filter].copy()

# Combined chart
st.subheader(f"Claims Amount Forecast - {product_filter}")

fig = go.Figure()

# Actual data
fig.add_trace(go.Scatter(x=actuals_filtered['MONTH'], y=actuals_filtered['TOTAL_ESTIMATED_AMOUNT'],
                         mode='lines+markers', name='Actual',
                         line=dict(color='#667eea', width=2.5),
                         marker=dict(size=5)))

# Forecast
fig.add_trace(go.Scatter(x=forecast_filtered['MONTH'], y=forecast_filtered['FORECAST'],
                         mode='lines+markers', name='Forecast',
                         line=dict(color='#e94560', width=2.5, dash='dash'),
                         marker=dict(size=7, symbol='diamond')))

# Confidence interval
fig.add_trace(go.Scatter(x=forecast_filtered['MONTH'], y=forecast_filtered['UPPER_BOUND'],
                         mode='lines', name='Upper Bound (95%)',
                         line=dict(color='rgba(233,69,96,0.3)'), showlegend=False))
fig.add_trace(go.Scatter(x=forecast_filtered['MONTH'], y=forecast_filtered['LOWER_BOUND'],
                         mode='lines', name='Confidence Interval',
                         fill='tonexty', line=dict(color='rgba(233,69,96,0.3)'),
                         fillcolor='rgba(233,69,96,0.1)'))

fig.update_layout(height=450, template='plotly_white',
                  xaxis_title='Month', yaxis_title='Estimated Claim Amount ($)',
                  legend=dict(orientation='h', yanchor='bottom', y=1.02))
st.plotly_chart(fig, use_container_width=True)

# All products comparison
st.subheader("Forecast Comparison Across Products")
col_l, col_r = st.columns(2)

with col_l:
    forecast_summary = session.sql("""
        SELECT SERIES AS PRODUCT_TYPE, SUM(FORECAST) AS FORECAST
        FROM ALTERYX_INSURANCE_DB.PUBLIC.CLAIMS_FORECAST_RESULTS
        GROUP BY SERIES
        ORDER BY FORECAST DESC
    """).to_pandas()
    fig2 = go.Figure(data=[
        go.Bar(x=forecast_summary['PRODUCT_TYPE'].tolist(),
               y=forecast_summary['FORECAST'].tolist(),
               marker_color=['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854'])
    ])
    fig2.update_layout(height=350, template='plotly_white', title='Total Forecasted Amount by Product (Next 6 Months)',
                       xaxis_title='Product Type', yaxis_title='Forecasted Amount ($)')
    st.plotly_chart(fig2, use_container_width=True)

with col_r:
    # Forecast uncertainty
    uncertainty_avg = session.sql("""
        SELECT SERIES AS PRODUCT_TYPE, AVG(UPPER_BOUND - LOWER_BOUND) AS UNCERTAINTY
        FROM ALTERYX_INSURANCE_DB.PUBLIC.CLAIMS_FORECAST_RESULTS
        GROUP BY SERIES
        ORDER BY UNCERTAINTY DESC
    """).to_pandas()
    fig3 = go.Figure(data=[
        go.Bar(x=uncertainty_avg['PRODUCT_TYPE'].tolist(),
               y=uncertainty_avg['UNCERTAINTY'].tolist(),
               marker_color=['#a1c9f4','#ffb482','#8de5a1','#ff9f9b','#d0bbff'])
    ])
    fig3.update_layout(height=350, template='plotly_white', title='Average Prediction Uncertainty by Product',
                       xaxis_title='Product Type', yaxis_title='Confidence Interval Width ($)')
    st.plotly_chart(fig3, use_container_width=True)

# AI Forecast Insights
st.divider()
st.subheader("AI Forecast Insights")

if st.button("Generate Forecast Analysis", type="primary"):
    with st.spinner("Analyzing forecast patterns with Cortex AI..."):
        forecast_summary_text = forecast_df.groupby('PRODUCT_TYPE').agg({
            'FORECAST': ['mean', 'sum'],
            'LOWER_BOUND': 'mean',
            'UPPER_BOUND': 'mean'
        }).reset_index().to_string()
        
        result = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
                'You are an insurance analytics forecasting expert. Analyze these 6-month claims forecast results and provide strategic insights in 4-5 sentences. Highlight which product lines show growth, which show decline, and recommend actions for capacity planning.
                
Forecast data summary:
{forecast_summary_text}

Provide strategic forecasting insights and capacity planning recommendations.') AS INSIGHTS
        """).to_pandas()
        st.markdown(f"""<div class="forecast-insight">{result['INSIGHTS'].iloc[0]}</div>""", unsafe_allow_html=True)
