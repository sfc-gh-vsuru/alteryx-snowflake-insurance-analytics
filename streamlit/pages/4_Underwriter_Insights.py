import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Underwriter Insights", layout="wide")

session = get_active_session()

st.markdown("""
<style>
    .coaching-box {
        background: linear-gradient(135deg, #e0f7fa, #b2ebf2);
        border-left: 5px solid #00838f;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .leaderboard-gold { color: #FFD700; font-size: 1.5rem; }
    .leaderboard-silver { color: #C0C0C0; font-size: 1.3rem; }
    .leaderboard-bronze { color: #CD7F32; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

st.title("Underwriter Performance Hub")
st.caption("Individual Performance Analytics & AI-Powered Coaching Recommendations")

# Fetch underwriter data
uwp_df = session.sql("""
    SELECT * FROM ALTERYX_INSURANCE_DB.PUBLIC.UNDERWRITER_PERFORMANCE
    ORDER BY APPROVAL_RATE DESC
""").to_pandas()

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Underwriters", f"{uwp_df.shape[0]}")
with col2:
    st.metric("Avg Approval Rate", f"{uwp_df['APPROVAL_RATE'].mean():.0f}%")
with col3:
    st.metric("Avg Risk Score", f"{uwp_df['AVG_RISK_SCORE'].mean():.1f}")
with col4:
    st.metric("Total Policies", f"{uwp_df['POLICY_COUNT'].sum():,.0f}")

st.divider()

# Leaderboard and radar chart
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Underwriter Leaderboard")
    leaderboard = uwp_df[['UNDERWRITER_NAME', 'SPECIALIZATION', 'APPROVAL_RATE', 
                           'POLICY_COUNT', 'EXPERIENCE_YEARS', 'AVG_RISK_SCORE']].head(10)
    st.dataframe(leaderboard, use_container_width=True)

with col_right:
    st.subheader("Performance Comparison (Radar)")
    selected_uws = st.multiselect("Select Underwriters to Compare", 
                                   uwp_df['UNDERWRITER_NAME'].tolist(), 
                                   default=uwp_df['UNDERWRITER_NAME'].head(3).tolist())
    
    if selected_uws:
        categories = ['Approval Rate', 'Policy Count (norm)', 'Experience', 'Risk Score (inv)', 'Review Flag Rate (inv)']
        fig = go.Figure()
        
        for uw_name in selected_uws:
            uw = uwp_df[uwp_df['UNDERWRITER_NAME'] == uw_name].iloc[0]
            values = [
                uw['APPROVAL_RATE'] / 100,
                uw['POLICY_COUNT'] / uwp_df['POLICY_COUNT'].max(),
                uw['EXPERIENCE_YEARS'] / uwp_df['EXPERIENCE_YEARS'].max(),
                1 - (uw['AVG_RISK_SCORE'] / 100),
                1 - (uw['REVIEW_FLAG_RATE'] / uwp_df['REVIEW_FLAG_RATE'].max()) if uwp_df['REVIEW_FLAG_RATE'].max() > 0 else 0.5
            ]
            fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name=uw_name))
        
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                         height=400, template='plotly_white', showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

# Scatter plot
st.subheader("Approval Rate vs Risk Score by Specialization")
specs = uwp_df['SPECIALIZATION'].unique().tolist()
colors = ['#e41a1c','#377eb8','#4daf4a','#984ea3','#ff7f00']
fig2 = go.Figure()
for i, spec in enumerate(specs):
    subset = uwp_df[uwp_df['SPECIALIZATION'] == spec]
    fig2.add_trace(go.Scatter(
        x=subset['AVG_RISK_SCORE'].tolist(),
        y=subset['APPROVAL_RATE'].tolist(),
        mode='markers', name=spec,
        marker=dict(size=14, color=colors[i % len(colors)], opacity=0.8),
        text=subset['UNDERWRITER_NAME'].tolist(),
        hovertemplate='%{text}<br>Risk: %{x:.1f}<br>Approval: %{y}%<extra></extra>'
    ))
fig2.update_layout(height=350, template='plotly_white',
                   xaxis_title='Average Risk Score', yaxis_title='Approval Rate (%)')
st.plotly_chart(fig2, use_container_width=True)

# AI Coaching
st.divider()
st.subheader("AI Performance Coaching")

selected_uw = st.selectbox("Select Underwriter for AI Coaching", uwp_df['UNDERWRITER_NAME'].tolist())

if st.button("Generate Coaching Feedback", type="primary"):
    uw = uwp_df[uwp_df['UNDERWRITER_NAME'] == selected_uw].iloc[0]
    with st.spinner("Generating personalized coaching with Cortex AI..."):
        result = session.sql(f"""
            SELECT ALTERYX_INSURANCE_DB.PUBLIC.UNDERWRITER_COACHING(
                '{selected_uw}', '{uw['SPECIALIZATION']}',
                {int(uw['EXPERIENCE_YEARS'])}, {int(uw['POLICY_COUNT'])},
                {int(uw['APPROVAL_RATE'])}, {uw['AVG_RISK_SCORE']},
                {int(uw['HIGH_RISK'])}, {int(uw['REVIEW_FLAG_RATE'])},
                {uw['AVG_PREMIUM_ADJUSTMENT_PCT']}
            ) AS COACHING
        """).to_pandas()
        st.markdown(f"""<div class="coaching-box">{result['COACHING'].iloc[0]}</div>""", unsafe_allow_html=True)
