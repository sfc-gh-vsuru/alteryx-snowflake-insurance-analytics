# Setup Guide

Step-by-step instructions to deploy the Insurance Analytics solution from scratch.

---

## Prerequisites

- Snowflake account with Cortex AI enabled ([region availability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability))
- Access to the source data (gold layer tables from upstream transformation pipeline)
- Alteryx Designer Cloud with Snowflake In-DB connector configured (for transformation layer)
- A role with `CREATE DATABASE`, `CREATE VIEW`, `CREATE FUNCTION`, `CREATE STAGE`, `CREATE STREAMLIT` privileges
- A warehouse (XSMALL is sufficient)

---

## Step 1: Create the Database and Schema

```sql
CREATE DATABASE IF NOT EXISTS <YOUR_DATABASE>;
USE DATABASE <YOUR_DATABASE>;
USE SCHEMA PUBLIC;
```

---

## Step 2: Create Views

These views point to the upstream gold layer tables. Replace `<SOURCE_DATABASE>.<SOURCE_SCHEMA>` with your actual source location.

```sql
CREATE OR REPLACE VIEW KPI_UNDERWRITING AS
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.KPI_UNDERWRITING;

CREATE OR REPLACE VIEW KPI_CLAIMS AS
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.KPI_CLAIMS;

CREATE OR REPLACE VIEW FRAUD_SUMMARY AS
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.FRAUD_SUMMARY;

CREATE OR REPLACE VIEW ADJUSTER_PERFORMANCE AS
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.ADJUSTER_PERFORMANCE;

CREATE OR REPLACE VIEW UNDERWRITER_PERFORMANCE AS
SELECT * FROM <SOURCE_DATABASE>.<SOURCE_SCHEMA>.UNDERWRITER_PERFORMANCE;
```

---

## Step 3: Create Internal Stage

```sql
CREATE STAGE IF NOT EXISTS INSURANCE_STAGE
  DIRECTORY = (ENABLE = TRUE);
```

---

## Step 4: Create Cortex AI UDFs

### 4.1 Executive KPI Narrative Generator

```sql
CREATE OR REPLACE FUNCTION GENERATE_KPI_NARRATIVE(
    p_month VARCHAR,
    p_product_type VARCHAR,
    p_policy_count NUMBER,
    p_approval_rate NUMBER,
    p_avg_risk_score FLOAT,
    p_avg_premium FLOAT,
    p_avg_coverage FLOAT
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
    SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
        'You are an insurance analytics executive advisor. Generate a concise 3-4 sentence executive summary for the following underwriting KPIs. Be specific with numbers and trends. Use professional insurance terminology.

Month: ' || p_month || '
Product Type: ' || p_product_type || '
Policy Count: ' || p_policy_count::VARCHAR || '
Approval Rate: ' || p_approval_rate::VARCHAR || '%
Average Risk Score: ' || ROUND(p_avg_risk_score, 1)::VARCHAR || '
Average Premium: $' || ROUND(p_avg_premium, 0)::VARCHAR || '
Average Coverage: $' || ROUND(p_avg_coverage, 0)::VARCHAR || '

Provide an executive narrative highlighting performance, risk posture, and any concerns.')
$$;
```

### 4.2 Fraud Risk Assessment

```sql
CREATE OR REPLACE FUNCTION FRAUD_RISK_ASSESSMENT(
    p_product_type VARCHAR,
    p_claim_type VARCHAR,
    p_claim_count NUMBER,
    p_total_paid FLOAT,
    p_estimated_amount FLOAT,
    p_is_open NUMBER,
    p_is_declined NUMBER
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
    SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
        'You are a fraud detection specialist in insurance. Analyze the following fraud summary data and provide a risk assessment in 3-4 sentences. Identify red flags, patterns of concern, and recommended investigation actions.

Product Type: ' || p_product_type || '
Claim Type: ' || p_claim_type || '
Claim Count: ' || p_claim_count::VARCHAR || '
Total Paid: $' || ROUND(p_total_paid, 0)::VARCHAR || '
Estimated Amount: $' || ROUND(p_estimated_amount, 0)::VARCHAR || '
Payout vs Estimate Ratio: ' || ROUND(p_total_paid / NULLIF(p_estimated_amount, 0) * 100, 1)::VARCHAR || '%
Open Claims: ' || p_is_open::VARCHAR || '
Declined Claims: ' || p_is_declined::VARCHAR || '

Provide a fraud risk assessment with severity level (LOW/MEDIUM/HIGH/CRITICAL) and recommended actions.')
$$;
```

### 4.3 Claims Triage Recommendation

```sql
CREATE OR REPLACE FUNCTION CLAIMS_TRIAGE_RECOMMENDATION(
    p_claim_type VARCHAR,
    p_product_type VARCHAR,
    p_high_priority NUMBER,
    p_fraud_flag NUMBER,
    p_avg_days_to_report FLOAT,
    p_avg_payout_ratio FLOAT,
    p_estimated_amount FLOAT,
    p_approved_amount FLOAT
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
    SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
        'You are a claims triage specialist. Based on the following claim segment data, provide a triage recommendation in 3-4 sentences. Include priority classification (P1-URGENT / P2-HIGH / P3-MEDIUM / P4-LOW), recommended actions, and resource allocation suggestion.

Claim Type: ' || p_claim_type || '
Product Type: ' || p_product_type || '
High Priority Claims: ' || p_high_priority::VARCHAR || '
Fraud Flagged: ' || p_fraud_flag::VARCHAR || '
Avg Days to Report: ' || ROUND(p_avg_days_to_report, 1)::VARCHAR || '
Avg Payout Ratio: ' || ROUND(p_avg_payout_ratio, 1)::VARCHAR || '%
Estimated Amount: $' || ROUND(p_estimated_amount, 0)::VARCHAR || '
Approved Amount: $' || ROUND(p_approved_amount, 0)::VARCHAR || '

Provide triage classification and recommended next steps.')
$$;
```

### 4.4 Underwriter Coaching

```sql
CREATE OR REPLACE FUNCTION UNDERWRITER_COACHING(
    p_name VARCHAR,
    p_specialization VARCHAR,
    p_experience_years NUMBER,
    p_policy_count NUMBER,
    p_approval_rate NUMBER,
    p_avg_risk_score FLOAT,
    p_high_risk NUMBER,
    p_review_flag_rate NUMBER,
    p_avg_premium_adjustment FLOAT
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
    SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
        'You are a senior underwriting manager providing personalized coaching feedback. Based on the following underwriter performance data, provide constructive coaching in 4-5 sentences. Include strengths, areas for improvement, and specific actionable recommendations.

Underwriter: ' || p_name || '
Specialization: ' || p_specialization || '
Experience: ' || p_experience_years::VARCHAR || ' years
Policies Processed: ' || p_policy_count::VARCHAR || '
Approval Rate: ' || p_approval_rate::VARCHAR || '%
Average Risk Score: ' || ROUND(p_avg_risk_score, 1)::VARCHAR || '
High Risk Policies: ' || p_high_risk::VARCHAR || '
Review Flag Rate: ' || p_review_flag_rate::VARCHAR || '%
Avg Premium Adjustment: ' || ROUND(p_avg_premium_adjustment, 1)::VARCHAR || '%

Provide personalized coaching feedback with specific recommendations.')
$$;
```

### 4.5 Adjuster Workload Analysis

```sql
CREATE OR REPLACE FUNCTION ADJUSTER_WORKLOAD_ANALYSIS(
    p_adjuster_id NUMBER,
    p_region VARCHAR,
    p_claim_count NUMBER,
    p_open NUMBER,
    p_settled NUMBER,
    p_high_priority NUMBER,
    p_settlement_rate NUMBER,
    p_avg_days_to_report FLOAT,
    p_avg_payout_pct FLOAT
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
    SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
        'You are a claims operations manager analyzing adjuster workload. Based on the following performance data, provide a workload assessment in 3-4 sentences. Include workload status (OVERLOADED / OPTIMAL / UNDERUTILIZED), efficiency observations, and rebalancing recommendations.

Adjuster ID: ' || p_adjuster_id::VARCHAR || '
Region: ' || p_region || '
Total Claims: ' || p_claim_count::VARCHAR || '
Open Claims: ' || p_open::VARCHAR || '
Settled Claims: ' || p_settled::VARCHAR || '
High Priority: ' || p_high_priority::VARCHAR || '
Settlement Rate: ' || p_settlement_rate::VARCHAR || '%
Avg Days to Report: ' || ROUND(p_avg_days_to_report, 1)::VARCHAR || '
Avg Payout %: ' || ROUND(p_avg_payout_pct, 1)::VARCHAR || '%

Provide workload assessment and optimization recommendations.')
$$;
```

---

## Step 5: Create ML Models

### 5.1 Claims Forecasting Model

```sql
-- Training view
CREATE OR REPLACE VIEW CLAIMS_FORECAST_TRAINING AS
SELECT
    MONTH AS ts,
    PRODUCT_TYPE AS series,
    SUM(ESTIMATED_AMOUNT) AS total_estimated_amount
FROM KPI_CLAIMS
GROUP BY MONTH, PRODUCT_TYPE
ORDER BY MONTH;

-- Train the forecast model
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST CLAIMS_FORECAST_MODEL(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'CLAIMS_FORECAST_TRAINING'),
    SERIES_COLNAME => 'SERIES',
    TIMESTAMP_COLNAME => 'TS',
    TARGET_COLNAME => 'TOTAL_ESTIMATED_AMOUNT'
);

-- Generate 6-month forecast
CREATE OR REPLACE TABLE CLAIMS_FORECAST_RESULTS AS
SELECT * FROM TABLE(CLAIMS_FORECAST_MODEL!FORECAST(
    FORECASTING_PERIODS => 6,
    CONFIG_OBJECT => {'prediction_interval': 0.95}
));
```

### 5.2 Fraud Anomaly Detection Model

```sql
-- Training view (historical data for model training)
CREATE OR REPLACE VIEW FRAUD_ANOMALY_TRAINING AS
SELECT
    MONTH AS ts,
    PRODUCT_TYPE AS series,
    SUM(CLAIM_COUNT) AS fraud_claim_count
FROM FRAUD_SUMMARY
GROUP BY MONTH, PRODUCT_TYPE
ORDER BY MONTH;

-- Split: use older data for training, newer data for detection
CREATE OR REPLACE VIEW FRAUD_ANOMALY_TRAIN_SPLIT AS
SELECT ts, series, fraud_claim_count
FROM FRAUD_ANOMALY_TRAINING
WHERE ts < '2025-01-01';

CREATE OR REPLACE VIEW FRAUD_ANOMALY_TEST_SPLIT AS
SELECT ts, series, fraud_claim_count
FROM FRAUD_ANOMALY_TRAINING
WHERE ts >= '2025-01-01';

-- Train the anomaly detection model
CREATE OR REPLACE SNOWFLAKE.ML.ANOMALY_DETECTION FRAUD_ANOMALY_MODEL(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'FRAUD_ANOMALY_TRAIN_SPLIT'),
    SERIES_COLNAME => 'SERIES',
    TIMESTAMP_COLNAME => 'TS',
    TARGET_COLNAME => 'FRAUD_CLAIM_COUNT',
    LABEL_COLNAME => ''
);

-- Run anomaly detection on recent data
CREATE OR REPLACE TABLE FRAUD_ANOMALY_RESULTS AS
SELECT * FROM TABLE(FRAUD_ANOMALY_MODEL!DETECT_ANOMALIES(
    INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'FRAUD_ANOMALY_TEST_SPLIT'),
    SERIES_COLNAME => 'SERIES',
    TIMESTAMP_COLNAME => 'TS',
    TARGET_COLNAME => 'FRAUD_CLAIM_COUNT',
    CONFIG_OBJECT => {'prediction_interval': 0.95}
));
```

---

## Step 6: Create Semantic View

```sql
CREATE OR REPLACE SEMANTIC VIEW INSURANCE_ANALYTICS_SV
  TABLES (
    uw AS KPI_UNDERWRITING
      COMMENT = 'Monthly underwriting KPIs by product type',
    claims AS KPI_CLAIMS
      COMMENT = 'Monthly claims KPIs by claim type and product type',
    fraud AS FRAUD_SUMMARY
      COMMENT = 'Monthly fraud summary by product and claim type',
    adj AS ADJUSTER_PERFORMANCE
      PRIMARY KEY (ADJUSTER_ID)
      COMMENT = 'Claims adjuster performance metrics by region',
    uwp AS UNDERWRITER_PERFORMANCE
      PRIMARY KEY (UNDERWRITER_NAME)
      COMMENT = 'Individual underwriter performance metrics'
  )
  DIMENSIONS (
    uw.month_dim AS uw.MONTH COMMENT = 'Month of underwriting activity',
    uw.product_type_dim AS uw.PRODUCT_TYPE COMMENT = 'Insurance product type',
    claims.month_dim AS claims.MONTH COMMENT = 'Month of claim activity',
    claims.claim_type_dim AS claims.CLAIM_TYPE COMMENT = 'Claim type',
    claims.product_type_dim AS claims.PRODUCT_TYPE COMMENT = 'Insurance product type for claims',
    fraud.month_dim AS fraud.MONTH COMMENT = 'Month of fraud activity',
    fraud.product_type_dim AS fraud.PRODUCT_TYPE COMMENT = 'Product type for fraud claims',
    fraud.claim_type_dim AS fraud.CLAIM_TYPE COMMENT = 'Claim type for fraud',
    adj.adjuster_id_dim AS adj.ADJUSTER_ID COMMENT = 'Unique adjuster identifier',
    adj.region_dim AS adj.REGION COMMENT = 'Geographic region',
    uwp.underwriter_name_dim AS uwp.UNDERWRITER_NAME COMMENT = 'Name of underwriter',
    uwp.specialization_dim AS uwp.SPECIALIZATION COMMENT = 'Specialization area',
    uwp.experience_years_dim AS uwp.EXPERIENCE_YEARS COMMENT = 'Years of experience'
  )
  METRICS (
    uw.total_policies AS SUM(uw.POLICY_COUNT) COMMENT = 'Total policies processed',
    uw.total_approved AS SUM(uw.APPROVED) COMMENT = 'Total policies approved',
    uw.total_declined AS SUM(uw.DECLINED) COMMENT = 'Total policies declined',
    uw.avg_coverage AS AVG(uw.AVG_COVERAGE_AMOUNT) COMMENT = 'Average coverage amount',
    uw.avg_premium AS AVG(uw.AVG_PREMIUM_AMOUNT) COMMENT = 'Average premium amount',
    uw.avg_risk AS AVG(uw.AVG_RISK_SCORE) COMMENT = 'Average risk score',
    uw.avg_approval_rate AS AVG(uw.APPROVAL_RATE) COMMENT = 'Approval rate percentage',
    claims.total_estimated AS SUM(claims.ESTIMATED_AMOUNT) COMMENT = 'Total estimated claim amount',
    claims.total_approved_amt AS SUM(claims.APPROVED_AMOUNT) COMMENT = 'Total approved claim amount',
    claims.total_high_priority AS SUM(claims.HIGH_PRIORITY) COMMENT = 'Total high priority claims',
    claims.total_fraud AS SUM(claims.FRAUD) COMMENT = 'Total fraud-flagged claims',
    claims.total_settled AS SUM(claims.SETTLED) COMMENT = 'Total settled claims',
    claims.avg_days_report AS AVG(claims.AVG_DAYS_TO_REPORT) COMMENT = 'Average days to report a claim',
    fraud.total_fraud_claims AS SUM(fraud.CLAIM_COUNT) COMMENT = 'Total fraudulent claims',
    fraud.total_fraud_paid AS SUM(fraud.TOTAL_PAID) COMMENT = 'Total paid on fraud claims',
    fraud.total_open AS SUM(fraud.IS_OPEN) COMMENT = 'Open fraud claims count',
    fraud.total_declined AS SUM(fraud.IS_DECLINED) COMMENT = 'Declined fraud claims count',
    adj.total_adj_claims AS SUM(adj.CLAIM_COUNT) COMMENT = 'Total claims assigned to adjusters',
    adj.avg_settlement_rate AS AVG(adj.SETTLEMENT_RATE) COMMENT = 'Average settlement rate',
    adj.total_adj_paid AS SUM(adj.TOTAL_PAID) COMMENT = 'Total paid by adjusters',
    uwp.total_uwp_policies AS SUM(uwp.POLICY_COUNT) COMMENT = 'Total policies by underwriter',
    uwp.avg_uwp_approval AS AVG(uwp.APPROVAL_RATE) COMMENT = 'Average underwriter approval rate',
    uwp.avg_uwp_risk AS AVG(uwp.AVG_RISK_SCORE) COMMENT = 'Average risk score by underwriter'
  )
  AI_VERIFIED_QUERIES (
    vq1 AS (
      QUESTION 'What is the total number of policies by product type?'
      SQL 'SELECT uw.PRODUCT_TYPE, SUM(uw.POLICY_COUNT) AS TOTAL_POLICIES FROM KPI_UNDERWRITING uw GROUP BY uw.PRODUCT_TYPE ORDER BY TOTAL_POLICIES DESC'
    ),
    vq2 AS (
      QUESTION 'Which product type has the most fraud claims?'
      SQL 'SELECT fraud.PRODUCT_TYPE, SUM(fraud.CLAIM_COUNT) AS TOTAL_FRAUD_CLAIMS FROM FRAUD_SUMMARY fraud GROUP BY fraud.PRODUCT_TYPE ORDER BY TOTAL_FRAUD_CLAIMS DESC'
    ),
    vq3 AS (
      QUESTION 'What is the average settlement rate by region?'
      SQL 'SELECT adj.REGION, AVG(adj.SETTLEMENT_RATE) AS AVG_SETTLEMENT_RATE FROM ADJUSTER_PERFORMANCE adj GROUP BY adj.REGION ORDER BY AVG_SETTLEMENT_RATE DESC'
    ),
    vq4 AS (
      QUESTION 'Who are the top performing underwriters by approval rate?'
      SQL 'SELECT uwp.UNDERWRITER_NAME, uwp.SPECIALIZATION, uwp.APPROVAL_RATE, uwp.POLICY_COUNT FROM UNDERWRITER_PERFORMANCE uwp ORDER BY uwp.APPROVAL_RATE DESC LIMIT 5'
    ),
    vq5 AS (
      QUESTION 'How many high priority claims are there by product type?'
      SQL 'SELECT claims.PRODUCT_TYPE, SUM(claims.HIGH_PRIORITY) AS TOTAL_HIGH_PRIORITY FROM KPI_CLAIMS claims GROUP BY claims.PRODUCT_TYPE ORDER BY TOTAL_HIGH_PRIORITY DESC'
    )
  );
```

---

## Step 7: Deploy Streamlit Application

### 7.1 Upload App Files to Stage

Upload the following files to the internal stage:

```
@INSURANCE_STAGE/
├── streamlit_app.py
├── environment.yml
└── pages/
    ├── 1_Executive_Dashboard.py
    ├── 2_Fraud_Intelligence.py
    ├── 3_Claims_Triage.py
    ├── 4_Underwriter_Insights.py
    ├── 5_Forecasting.py
    ├── 6_Ask_Me_Anything.py
    └── 7_Adjuster_Workload.py
```

Using SQL PUT commands:

```sql
PUT 'file:///path/to/streamlit_app.py' @INSURANCE_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/environment.yml' @INSURANCE_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/1_Executive_Dashboard.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/2_Fraud_Intelligence.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/3_Claims_Triage.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/4_Underwriter_Insights.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/5_Forecasting.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/6_Ask_Me_Anything.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT 'file:///path/to/pages/7_Adjuster_Workload.py' @INSURANCE_STAGE/pages/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

### 7.2 Environment File

The `environment.yml` defines the Python dependencies for the Streamlit app:

```yaml
name: sf_env
channels:
  - snowflake
dependencies:
  - plotly
  - snowflake-snowpark-python
```

### 7.3 Create the Streamlit App

```sql
CREATE OR REPLACE STREAMLIT INSURANCE_ANALYTICS_APP
    ROOT_LOCATION = '@INSURANCE_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = '<YOUR_WAREHOUSE>'
    TITLE = 'Insurance Analytics - Cortex AI';
```

---

## Step 8: Grant Permissions

Grant access to additional roles as needed:

```sql
-- Grant to a consumer role
GRANT USAGE ON DATABASE <YOUR_DATABASE> TO ROLE <CONSUMER_ROLE>;
GRANT USAGE ON SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE <CONSUMER_ROLE>;
GRANT SELECT ON ALL VIEWS IN SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE <CONSUMER_ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE <CONSUMER_ROLE>;
GRANT USAGE ON ALL FUNCTIONS IN SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE <CONSUMER_ROLE>;
GRANT READ ON STAGE <YOUR_DATABASE>.PUBLIC.INSURANCE_STAGE TO ROLE <CONSUMER_ROLE>;
GRANT USAGE ON STREAMLIT <YOUR_DATABASE>.PUBLIC.INSURANCE_ANALYTICS_APP TO ROLE <CONSUMER_ROLE>;
GRANT SELECT ON SEMANTIC VIEW <YOUR_DATABASE>.PUBLIC.INSURANCE_ANALYTICS_SV TO ROLE <CONSUMER_ROLE>;
```

---

## Step 9: Verify Deployment

```sql
-- Check all objects exist
SHOW VIEWS IN SCHEMA <YOUR_DATABASE>.PUBLIC;
SHOW USER FUNCTIONS IN SCHEMA <YOUR_DATABASE>.PUBLIC;
SHOW TABLES IN SCHEMA <YOUR_DATABASE>.PUBLIC;
SHOW STREAMLITS IN SCHEMA <YOUR_DATABASE>.PUBLIC;
SHOW SEMANTIC VIEWS IN SCHEMA <YOUR_DATABASE>.PUBLIC;

-- Test a UDF
SELECT GENERATE_KPI_NARRATIVE('2025-01-01', 'AUTO', 137, 64, 46.1, 3957, 58325);

-- Test ML forecast results
SELECT * FROM CLAIMS_FORECAST_RESULTS LIMIT 5;

-- Test anomaly detection results
SELECT * FROM FRAUD_ANOMALY_RESULTS WHERE IS_ANOMALY = TRUE;
```

---

## Notes

- **LLM Model:** All UDFs use `mistral-large2`. If your account has access to other models (e.g., `claude-3-5-sonnet`, `llama3.1-70b`), you can substitute by replacing the model name in each UDF.
- **ML Models:** The anomaly detection model requires a train/test time split. Data before 2025 is used for training; 2025+ data is evaluated for anomalies.
- **Streamlit Packages:** Ensure `plotly` is added to the SiS app packages (via environment.yml or the Packages panel in Snowsight).
- **Plotly Compatibility:** Use `plotly.graph_objects` (`go.Figure`, `go.Bar`, `go.Scatter`) instead of `plotly.express` (`px.bar`, `px.scatter`, `px.pie`) for reliable rendering in Streamlit in Snowflake.

---

## Security Considerations

> **This repository contains NO credentials, passwords, API keys, or secrets.**

- All configuration values (database names, roles, warehouses) are parameterized as placeholders
- The Streamlit app uses `get_active_session()` -- inherits the caller's session with no embedded credentials
- UDFs reference Cortex functions via fully-qualified names with no authentication tokens
- Data access is governed by Snowflake RBAC -- the app only sees what the executing role is granted
- Source data is read-only by design -- transformation outputs are written to separate schemas
