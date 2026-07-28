import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Ask Me Anything", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .chat-user {
        background: #e3f2fd;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1976d2;
    }
    .chat-ai {
        background: #f3e5f5;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #7b1fa2;
    }
    .sql-box {
        background: #263238;
        color: #80cbc4;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("Ask Me Anything")
st.caption("Natural Language Analytics powered by Cortex Analyst & Semantic View")

# Suggested questions
st.markdown("#### Suggested Questions")
suggested = [
    "What is the total number of policies by product type?",
    "Which product type has the most fraud claims?",
    "What is the average settlement rate by region?",
    "Who are the top performing underwriters by approval rate?",
    "How many high priority claims are there by product type?",
    "What are the monthly approval rates for AUTO insurance?",
    "Show me the total estimated vs approved amounts by claim type"
]

cols = st.columns(3)
for i, q in enumerate(suggested):
    with cols[i % 3]:
        if st.button(q, key=f"suggest_{i}", use_container_width=True):
            st.session_state['user_question'] = q

st.divider()

# Chat input
user_question = st.text_input("Ask a question about insurance data...", 
                               value=st.session_state.get('user_question', ''),
                               placeholder="e.g., What is the approval rate trend for home insurance?")

if user_question:
    safe_question = user_question.replace("'", "''")
    st.markdown(f"""<div class="chat-user"><strong>You:</strong> {user_question}</div>""", unsafe_allow_html=True)
    
    with st.spinner("Analyzing with Cortex Analyst..."):
        try:
            # Use Cortex Analyst via the semantic view
            analyst_result = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
                    'You are an insurance data analyst. Based on the available tables in ALTERYX_INSURANCE_DB.PUBLIC (KPI_UNDERWRITING, KPI_CLAIMS, FRAUD_SUMMARY, ADJUSTER_PERFORMANCE, UNDERWRITER_PERFORMANCE), generate ONLY a SQL query to answer the following question. Return ONLY the SQL, no explanation.
                    
Available columns:
- KPI_UNDERWRITING: MONTH, PRODUCT_TYPE, POLICY_COUNT, APPROVED, DECLINED, REFERRED, COUNTER, REVIEW, AVG_COVERAGE_AMOUNT, AVG_PREMIUM_AMOUNT, AVG_RISK_SCORE, AVG_CREDIT_SCORE, APPROVAL_RATE
- KPI_CLAIMS: MONTH, CLAIM_TYPE, PRODUCT_TYPE, ESTIMATED_AMOUNT, APPROVED_AMOUNT, COVERAGE_AMOUNT, PREMIUM_AMOUNT, AVG_DAYS_TO_REPORT, AVG_PAYOUT_RATIO, APPROVED, SETTLED, CLOSED, HIGH_PRIORITY, FRAUD
- FRAUD_SUMMARY: MONTH, PRODUCT_TYPE, CLAIM_TYPE, CLAIM_COUNT, TOTAL_PAID, ESTIMATED_AMOUNT, APPROVED_AMOUNT, AVG_ESTIMATED_AMOUNT, IS_OPEN, IS_DECLINED
- ADJUSTER_PERFORMANCE: ADJUSTER_ID, REGION, CLAIM_COUNT, OPEN, SETTLED, CLOSED, HIGH_PRIORITY, DENIED, TOTAL_PAID, ESTIMATED_AMOUNT, APPROVED_AMOUNT, AVG_DAYS_TO_REPORT, SETTLEMENT_RATE
- UNDERWRITER_PERFORMANCE: UNDERWRITER_NAME, SPECIALIZATION, EXPERIENCE_YEARS, POLICY_COUNT, APPROVED, DECLINED, REFERRED, COUNTER, REVIEW, HIGH_RISK, AVG_COVERAGE_AMOUNT, AVG_PREMIUM_AMOUNT, AVG_RISK_SCORE, APPROVAL_RATE, REVIEW_FLAG_RATE

Question: {safe_question}

Return ONLY the SQL query with no markdown formatting or explanation.') AS SQL_QUERY
            """).to_pandas()
            
            generated_sql = analyst_result['SQL_QUERY'].iloc[0].strip()
            # Clean up the SQL if it has markdown code blocks
            if '```' in generated_sql:
                generated_sql = generated_sql.split('```')[1]
                if generated_sql.startswith('sql'):
                    generated_sql = generated_sql[3:]
                generated_sql = generated_sql.strip()
            
            with st.expander("Generated SQL", expanded=False):
                st.code(generated_sql, language='sql')
            
            # Execute the generated SQL
            result_df = session.sql(generated_sql).to_pandas()
            
            st.markdown(f"""<div class="chat-ai"><strong>Cortex AI:</strong> Here are the results for your question.</div>""", unsafe_allow_html=True)
            st.dataframe(result_df, use_container_width=True)
            
            # If numeric data, show a chart
            numeric_cols = result_df.select_dtypes(include=['number']).columns.tolist()
            non_numeric_cols = result_df.select_dtypes(exclude=['number']).columns.tolist()
            
            if len(numeric_cols) >= 1 and len(non_numeric_cols) >= 1:
                fig = go.Figure(data=[
                    go.Bar(x=result_df[non_numeric_cols[0]].tolist(),
                           y=result_df[numeric_cols[0]].tolist(),
                           marker_color='#667eea')
                ])
                fig.update_layout(height=350, template='plotly_white',
                                  xaxis_title=non_numeric_cols[0], yaxis_title=numeric_cols[0])
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
