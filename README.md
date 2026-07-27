# Insurance Analytics with Snowflake Cortex AI & Alteryx

## The Power of Two Platforms

### Snowflake AI Data Cloud

Snowflake's AI Data Cloud is the foundation of modern data intelligence. It unifies data storage, processing, and AI under a single governed platform -- enabling organizations to mobilize their data for analytics, machine learning, and generative AI without the complexity of managing infrastructure. With native capabilities like Cortex AI (large language models, ML functions, and Cortex Analyst), Snowflake transforms how enterprises extract value from data -- bringing AI directly to where the data lives, securely and at scale.

Key capabilities leveraged in this solution:
- **Cortex LLM Functions** -- In-database generative AI using models like `claude-3-5-sonnet` for natural language generation, risk assessment, and personalized recommendations
- **Cortex ML Functions** -- Native time-series forecasting and anomaly detection without external tooling
- **Cortex Analyst** -- Natural language to SQL, enabling business users to ask questions in plain English
- **Snowflake Secure Data Sharing** -- Zero-copy data sharing between partners with automatic incremental sync
- **Streamlit in Snowflake** -- Interactive applications deployed natively within the Snowflake ecosystem

### Alteryx Platform

Alteryx is the leading analytics automation platform that empowers business users and data professionals to transform raw data into actionable insights through intuitive, no-code/low-code workflows. Alteryx bridges the gap between raw data complexity and business decision-making -- enabling citizen data scientists and analysts to build repeatable, governed data pipelines without deep technical expertise.

Key capabilities leveraged in this solution:
- **Visual Workflow Designer** -- Drag-and-drop data transformation and enrichment
- **Snowflake Native Connector** -- Direct read/write to Snowflake with pushdown optimization
- **Data Quality & Preparation** -- Cleansing, deduplication, and standardization at scale
- **Business Logic Automation** -- Repeatable workflows that encode domain expertise into data pipelines

---

## Solution Overview

This solution demonstrates how **Alteryx** and **Snowflake** work together to deliver an end-to-end insurance analytics platform powered by AI.

**The Data Flow:**

Alteryx connects directly to Snowflake and reads raw insurance data from the bronze layer -- policy submissions, claims filings, adjuster notes, underwriting decisions, and fraud indicators. Through visual workflows designed by insurance business analysts, Alteryx transforms, cleanses, and enriches this raw data, applying business rules specific to insurance underwriting and claims operations. The transformed outputs are written back to Snowflake as curated silver and gold layer tables, organized for analytical consumption.

In this implementation, the insurance business persona uses Alteryx to:
1. Define and execute data transformation workflows on raw policy and claims data
2. Apply domain-specific business rules (risk scoring logic, claims categorization, fraud flagging criteria)
3. Publish curated, analytics-ready datasets back to Snowflake via secure data sharing

Once the gold layer data lands in Snowflake (via the Alteryx partner share), Snowflake Cortex AI takes over -- applying large language models, machine learning, and natural language analytics to deliver intelligent insights through an interactive Streamlit dashboard.

---

## Alteryx Solution Deep Dive

> *[Section reserved for detailed Alteryx workflow documentation, transformation logic, and business rule implementation]*

---

## Alteryx and Snowflake - Joint Architecture

> *[Section reserved for joint architecture diagram, data flow specifications, and integration patterns]*

---

## Business Use Cases

This platform demonstrates **7 AI-powered insurance analytics use cases**, each showcasing a distinct Snowflake Cortex AI capability:

| # | Use Case | AI Capability | Business Value |
|---|----------|---------------|----------------|
| 1 | Executive KPI Narratives | Cortex LLM (claude-3-5-sonnet) | Automated boardroom-ready summaries from raw metrics |
| 2 | Fraud Intelligence Center | ML Anomaly Detection + LLM | Proactive fraud pattern detection and risk assessment |
| 3 | Claims Triage Command Center | Cortex LLM | AI-assisted prioritization and resource allocation |
| 4 | Underwriter Performance Coaching | Cortex LLM | Personalized AI coaching at scale |
| 5 | Predictive Claims Forecasting | Cortex ML Forecast | 6-month claims volume prediction with confidence intervals |
| 6 | Natural Language Analytics | Cortex Analyst (Semantic View) | Zero-SQL querying for business users |
| 7 | Adjuster Workload Optimization | Cortex LLM | AI-driven workforce rebalancing recommendations |

---

## Data Architecture

### Source: Alteryx Partner Share

The curated gold layer data is shared from Alteryx via Snowflake Secure Data Sharing:

```
ALTERYX_SHARE.INSURANCE_UNDERWRITING_ANALYTICS
├── KPI_UNDERWRITING        (140 rows) -- Monthly underwriting KPIs by product type
├── KPI_CLAIMS              (371 rows) -- Monthly claims metrics by claim & product type
├── FRAUD_SUMMARY           (68 rows)  -- Fraud-specific claim aggregations
├── ADJUSTER_PERFORMANCE    (30 rows)  -- Claims adjuster workload & efficiency
└── UNDERWRITER_PERFORMANCE (25 rows)  -- Individual underwriter metrics
```

### Target: ALTERYX_INSURANCE_DB

Views in the target database point directly to the partner share, ensuring **automatic incremental updates** -- when Alteryx refreshes the share, all downstream analytics reflect the latest data instantly with zero ETL.

```
ALTERYX_INSURANCE_DB.PUBLIC
├── Views (auto-sync from partner share)
│   ├── KPI_UNDERWRITING
│   ├── KPI_CLAIMS
│   ├── FRAUD_SUMMARY
│   ├── ADJUSTER_PERFORMANCE
│   └── UNDERWRITER_PERFORMANCE
├── ML Model Results
│   ├── CLAIMS_FORECAST_RESULTS    -- 6-month forecast by product type
│   └── FRAUD_ANOMALY_RESULTS      -- Anomaly detection on fraud patterns
├── Semantic View
│   └── INSURANCE_ANALYTICS_SV     -- Cortex Analyst natural language interface
├── Stage
│   └── INSURANCE_STAGE            -- App files + semantic model YAML
└── Streamlit App
    └── INSURANCE_ANALYTICS_APP    -- 7-page interactive dashboard
```

### Data Dimensions

- **Product Types:** AUTO, COMMERCIAL, HEALTH, HOME, LIFE
- **Claim Types:** COLLISION, FIRE, LIABILITY, MEDICAL, PROPERTY, THEFT, WATER
- **Regions:** Pacific Northwest, Southeast, West, Midwest, Northeast, Southwest
- **Time Range:** 2023 -- 2025 (monthly granularity)

---

## Cortex AI Components

### UDFs (User-Defined Functions)

Five SQL UDFs powered by `claude-3-5-sonnet` provide on-demand AI analysis:

| UDF | Purpose | Inputs |
|-----|---------|--------|
| `GENERATE_KPI_NARRATIVE` | Executive summary generation from monthly KPIs | month, product_type, metrics |
| `FRAUD_RISK_ASSESSMENT` | Fraud risk commentary with severity classification | product_type, claim_type, amounts, status |
| `CLAIMS_TRIAGE_RECOMMENDATION` | Priority classification (P1-P4) with action items | claim_type, priority, fraud_flag, days, amounts |
| `UNDERWRITER_COACHING` | Personalized performance coaching feedback | name, specialization, rates, scores, experience |
| `ADJUSTER_WORKLOAD_ANALYSIS` | Workload status and rebalancing recommendations | adjuster_id, region, claims, rates |

### ML Models

| Model | Type | Training Data | Output |
|-------|------|---------------|--------|
| `CLAIMS_FORECAST_MODEL` | SNOWFLAKE.ML.FORECAST | Claims amounts by product (monthly) | 6-month predictions + 95% confidence intervals |
| `FRAUD_ANOMALY_MODEL` | SNOWFLAKE.ML.ANOMALY_DETECTION | Fraud claim counts by product (pre-2025) | Anomaly flags on 2025+ data with percentiles |

### Semantic View

`INSURANCE_ANALYTICS_SV` enables Cortex Analyst natural language querying across all 5 source tables:
- 13 dimensions (month, product type, claim type, region, underwriter name, specialization, etc.)
- 23 metrics (policy counts, amounts, rates, fraud counts, settlement rates, etc.)
- 5 verified queries for onboarding users

---

## Streamlit Application

### App: INSURANCE_ANALYTICS_APP

A multi-page Streamlit in Snowflake application with polished visualizations:

```
streamlit_app.py                    -- Landing page with navigation
pages/
├── 1_Executive_Dashboard.py        -- KPI cards, trend charts, AI narratives
├── 2_Fraud_Intelligence.py         -- Heatmaps, anomaly viz, AI risk assessment
├── 3_Claims_Triage.py              -- Priority matrix, distribution, AI triage
├── 4_Underwriter_Insights.py       -- Radar charts, leaderboard, AI coaching
├── 5_Forecasting.py                -- ML forecast with confidence bands
├── 6_Ask_Me_Anything.py            -- Natural language Q&A interface
└── 7_Adjuster_Workload.py          -- Regional analysis, AI workload optimization
```

### Visual Design
- Interactive Plotly charts (area, line, bar, scatter, pie, radar, heatmap)
- Color-coded KPI metric cards with performance indicators
- Custom CSS styling with gradient headers and card-based layouts
- On-demand AI generation via button triggers (avoids unnecessary LLM calls)

---

## Access & Permissions

This solution uses a **least-privilege** access model. Replace the placeholder role names below with roles appropriate to your organization:

| Role (Configurable) | Access Level |
|---------------------|-------------|
| `<DEPLOYER_ROLE>` | Owner -- full control on all objects (used for initial deployment) |
| `<CONSUMER_ROLE>` | Granted USAGE/SELECT on all views, tables, UDFs, stage, Streamlit app, and semantic view |

> **Note:** In production, avoid using `ACCOUNTADMIN` for day-to-day access. Create a dedicated functional role with only the privileges required for this application.

### Recommended RBAC Setup

```sql
-- Create a dedicated role for this application
CREATE ROLE IF NOT EXISTS INSURANCE_ANALYTICS_ROLE;

-- Grant necessary privileges
GRANT USAGE ON DATABASE <YOUR_DATABASE> TO ROLE INSURANCE_ANALYTICS_ROLE;
GRANT USAGE ON SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE INSURANCE_ANALYTICS_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE INSURANCE_ANALYTICS_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE INSURANCE_ANALYTICS_ROLE;
GRANT USAGE ON ALL FUNCTIONS IN SCHEMA <YOUR_DATABASE>.PUBLIC TO ROLE INSURANCE_ANALYTICS_ROLE;
GRANT USAGE ON STREAMLIT <YOUR_DATABASE>.PUBLIC.<YOUR_STREAMLIT_APP> TO ROLE INSURANCE_ANALYTICS_ROLE;
```

---

## Technical Setup

### Prerequisites
- Snowflake account with Cortex AI enabled (check [region availability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability))
- Access to the Alteryx partner share (or equivalent source data share)
- A warehouse with appropriate sizing (XSMALL is sufficient for this dataset)
- A role with `CREATE DATABASE`, `CREATE WAREHOUSE` privileges (for initial setup only)

### Configuration

The following values are configurable -- update them to match your environment:

| Parameter | Description | Example Value |
|-----------|-------------|---------------|
| `<SOURCE_SHARE>` | Alteryx partner share name | `ALTERYX_SHARE.INSURANCE_UNDERWRITING_ANALYTICS` |
| `<TARGET_DATABASE>` | Database for analytics objects | `ALTERYX_INSURANCE_DB` |
| `<WAREHOUSE>` | Compute warehouse | Any warehouse in your account |
| `<DEPLOYER_ROLE>` | Role that creates objects | A role with appropriate CREATE privileges |
| `<CONSUMER_ROLE>` | Role that accesses the app | A role granted to end users |

### Deployment
All objects are deployed in `<TARGET_DATABASE>.PUBLIC`:
- Views auto-sync from the Alteryx partner share
- UDFs call `SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', ...)` for LLM inference
- ML models are trained using `SNOWFLAKE.ML.FORECAST` and `SNOWFLAKE.ML.ANOMALY_DETECTION`
- Streamlit app files are stored on `@INSURANCE_STAGE` and served via `CREATE STREAMLIT`

### Dependencies (environment.yml)
```yaml
name: sf_env
channels:
  - snowflake
dependencies:
  - plotly
  - snowflake-snowpark-python
```

---

## Security Considerations

> **IMPORTANT:** This repository contains NO credentials, passwords, API keys, or secrets.

Before committing or sharing externally, verify the following checklist:

- [ ] No Snowflake account identifiers or URLs in code
- [ ] No usernames, passwords, or private keys
- [ ] No OAuth tokens or API keys
- [ ] No `.env` files or credential configuration files
- [ ] Role names are generalised (not org-specific privileged roles)
- [ ] Warehouse names are documented as configurable, not hardcoded to internal names

### Best Practices Applied
- All sensitive configuration is parameterized (database, role, warehouse names)
- The Streamlit app uses `get_active_session()` which inherits the caller's session -- no embedded credentials
- UDFs reference Cortex functions via fully-qualified names with no authentication tokens
- Data access is governed by Snowflake RBAC -- the app only sees what the executing role is granted
- The partner share is read-only by design -- no write-back risk to source data

---

## Summary

This solution demonstrates the power of combining **Alteryx** (business-driven data transformation) with **Snowflake Cortex AI** (in-database intelligence) to deliver a complete insurance analytics platform. The data flows from raw to insight without leaving the Snowflake ecosystem -- Alteryx handles the business logic and data curation, while Snowflake Cortex AI provides generative narratives, predictive forecasting, anomaly detection, and natural language access, all served through an interactive Streamlit dashboard.
