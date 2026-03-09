# NovaCred Credit Application Governance Analysis

> **DEGO 2606 - Data Ecosystems and Governance in Organizations**  
> MSc Business Analytics | Nova SBE  
> Group 14 – Credit Application Governance Analysis

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Repository Structure](#repository-structure)
3. [Team & Roles](#team--roles)
4. [Dataset](#dataset)
5. [Data Quality Findings](#data-quality-findings)
6. [Bias & Fairness Analysis](#bias--fairness-analysis)
7. [Privacy Assessment](#privacy-assessment)
8. [Governance Recommendations](#governance-recommendations)
9. [How to Run the Notebooks](#how-to-run-the-notebooks)
10. [Presentation](#presentation)

## Executive Summary

NovaCred is a fintech startup that uses machine learning to make credit decisions. Following a regulatory inquiry into potential discrimination in lending practices, our team conducted a full data governance audit of 502 raw credit applications.

**Key findings at a glance:**

| Area | Finding | Severity |
|------|---------|----------|
| Data Quality | 502 raw records → 498 clean records after deduplication and remediation | Medium |
| Gender Bias | Disparate Impact ratio of **0.767** - below the 0.8 four-fifths threshold | **High** |
| Age Bias | Age 18-30 DI ratio of **0.602** vs 41-50 group - well below threshold | **High** |
| Interaction Effect | Female + 18-30 approval rate: **31.1%** vs Male + 18-30: **52.7%** (DI = 0.591) | **Critical** |
| PII Exposure | **8 PII fields** identified, including unprotected SSNs and IP addresses | **Critical** |
| GDPR Gaps | **8 out of 8** assessed GDPR articles show compliance gaps | **Critical** |
| EU AI Act | NovaCred's model is classified as **High-Risk** under Annex III, Section 5(b) | **Critical** |

The dataset shows material evidence of gender- and age-based disparate impact in credit approvals. Female applicants were approved at 50.8% vs 66.3% for male applicants. This disparity persists after controlling for financial risk variables (income, DTI, credit history), indicating structural bias rather than a difference in creditworthiness. Additionally, the dataset stores highly sensitive PII (SSNs, IPs, full names) without any pseudonymization, consent tracking, or retention policy - violations of core GDPR principles.

## Repository Structure

```
DEGO_project-team14/
├── README.md                          # This file - executive summary & findings
├── data/
│   ├── raw_credit_applications.json   # Original dataset (500+ records)
│   └── credit_applications_clean_final.csv  # Cleaned output (498 records)
├── notebooks/
│   ├── 01-data-quality.ipynb          # Data Engineer: quality audit & remediation
│   ├── 02-bias-analysis.ipynb         # Data Scientist: bias detection & fairness metrics
│   └── 03-privacy-demo.ipynb          # Governance Officer: PII, GDPR, EU AI Act
├── src/
│   └── fairness_utils.py              # Reusable fairness metric helpers
└── presentation/
    └── VIDEO.md                       # 6-minute presentation video: https://youtu.be/
```

## Team & Roles

| Name | Student ID | Role | Responsibilities |
|------|-----------|------|-----------------|
| Philipp Connert | 66323 | Product Lead | Presentation, coordination, README documentation |
| Xavier Albino | 56363 | Data Engineer | Data loading, cleaning pipeline, quality audit (`01-data-quality.ipynb`) |
| Amgirus Murali | 75373 | Governance Officer | GDPR mapping, privacy demo, AI Act classification (`03-privacy-demo.ipynb`) |
| Othmane Chadi | 70269 | Data Scientist | Bias analysis, fairness metrics, statistical testing (`02-bias-analysis.ipynb`) |

## Dataset

**File:** `data/raw_credit_applications.json`  
**Records:** 502 (raw) → 498 (after cleaning)  
**Format:** Nested JSON with 6 top-level keys per record

| Field Group | Fields |
|-------------|--------|
| Applicant Info | `full_name`, `email`, `ssn`, `ip_address`, `gender`, `date_of_birth`, `zip_code` |
| Financials | `annual_income`, `credit_history_months`, `debt_to_income`, `savings_balance` |
| Spending Behavior | Array of `{category, amount}` objects |
| Decision | `loan_approved`, `interest_rate`, `approved_amount`, `rejection_reason` |

## Data Quality Findings

> **Notebook:** `notebooks/01-data-quality.ipynb`  
> **Owner:** Xavier Albino - Data Engineer

Analysis was structured across all six data quality dimensions: Completeness, Uniqueness, Consistency, Validity, Accuracy, and Timeliness.

### Summary Table

| Dimension | Issue | Affected Records | % | Remediation |
|-----------|-------|-----------------|---|-------------|
| Completeness | Hidden blank strings (empty strings ≠ null) | 14 | 2.79% | Replaced with `NaN` |
| Completeness | Missing `processing_timestamp` | 440 | 87.65% | Flagged as audit-trail gap |
| Completeness | Missing required fields (email, SSN, DOB, gender, zip) | 5-7 per field | 1-1.4% | Flagged; not imputed |
| Uniqueness | Duplicate application IDs (`_id`) | 4 records (2 groups) | 0.8% | Kept most complete / latest; 502 → 500 |
| Uniqueness | Duplicate SSNs across different applicants | 6 records (3 SSNs) | 1.2% | Resolved; 500 → 498 |
| Consistency | Mixed types in `annual_income` (int, float, string) | Multiple | - | Coerced to numeric |
| Consistency | Schema overlap: `annual_income` + `annual_salary` (same concept) | 5 records | 1.0% | Merged into single field |
| Consistency | Inconsistent gender coding (`M`/`Male`, `F`/`Female`) | 110 | 22.1% | Normalized to `Male`/`Female` |
| Consistency | Inconsistent date formats (3 formats: ISO, DD/MM/YYYY, YYYY/MM/DD) | 162 | 32.3% | Parsed and standardized to `datetime64` |
| Validity | Negative `credit_history_months` | 2 | 0.4% | Set to `NaN` |
| Validity | `debt_to_income` outside plausible range [0, 1.5] | 1 | 0.2% | Set to `NaN` |
| Validity | Negative `savings_balance` | 1 | 0.2% | Set to `NaN` |
| Validity | Malformed email addresses | 4 | 0.8% | Set to `NaN` |
| Accuracy | Future-dated `processing_timestamp` values | 2 | 0.4% | Flagged; not removed |
| Timeliness | Only 62 records have a timestamp | 440 missing | 87.6% | No meaningful recency assessment possible |

### Pipeline Output

After running the full cleaning pipeline:
- **Raw input:** 502 records
- **After `_id` deduplication:** 500 records (-2)
- **After SSN deduplication:** 498 records (-2)
- **Final clean dataset:** `data/credit_applications_clean_final.csv` (498 rows, 20 columns)

### Notable Issues

- **Hidden blank strings:** 14 fields stored as `""` (empty strings) were missed by standard `isna()` checks. Fields affected: `email` (7), `date_of_birth` (4), `gender` (2), `zip_code` (1).
- **SSN sharing across applicants:** Three SSNs appeared under different names (e.g., `780-24-9300` shared by Susan Martinez and Gary Wilson), indicating either a data integrity error or a fraud signal.
- **Decision field integrity:** All 6 structural checks pass - approved records have `approved_amount` + `interest_rate` populated; rejected records have `rejection_reason` populated.
- **Age range:** After parsing DOBs, all 494 parseable records fall within 21.2-65.3 years. No implausible ages detected.

## Bias & Fairness Analysis

> **Notebook:** `notebooks/02-bias-analysis.ipynb`  
> **Metric:** Disparate Impact (DI) = Unprivileged approval rate / Privileged approval rate  
> **Threshold:** DI < 0.8 triggers the "four-fifths rule" (potential disparate impact)

### 2.1 Gender Disparate Impact

| Group | Approval Rate | n |
|-------|-------------|---|
| Male | 66.26% | 246 |
| Female | 50.80% | 250 |
| **DI Ratio** | **0.767** | - |

**Result: DI = 0.767 - below the 0.8 threshold. Potential disparate impact confirmed.**

- Chi-square test: χ² = 11.58, p = 0.0007 (statistically significant)
- Demographic parity difference: **0.1546**
- Interest rate fairness: Female mean 4.49% vs Male 4.63% - *not* statistically significant (p = 0.31), suggesting pricing is fair among approved applicants, but the approval gate itself is biased.

### 2.2 Age-Based Bias

| Age Group | Approval Rate | n |
|-----------|-------------|---|
| 18-30 | 41.4% | 116 |
| 31-40 | 62.5% | 168 |
| 41-50 | 68.8% | 125 |
| 51-65 | 57.3% | 82 |

- Chi-square: χ² = 22.75, p = 0.0001 (significant)
- **Age DI (18-30 vs 41-50): 0.602 - well below 0.8. Younger applicants face potential disparate impact.**

### 2.3 Proxy Variable Analysis

We tested three candidate proxy variables using a two-condition framework:
1. **Condition 1:** Variable must be statistically associated with a protected attribute (gender)
2. **Condition 2:** Variable must predict approval *after* controlling for gender and financial risk

| Proxy Candidate | Condition 1 | Condition 2 | Verdict |
|-----------------|-------------|-------------|---------|
| ZIP/Region | YES (χ² = 319.2, p ≈ 0, ZIP `902` = 93.4% female) | NO (p = 0.82) | Not fully established |
| Spending behavior (flagged: Gambling, Alcohol, Adult Entertainment) | NO (p = 0.80) | NO (p = 0.62) | Not established |

**Structural proxy risk (ZIP):** Although ZIP code does not independently predict approval, the strong geographic gender clustering (ZIP `902` = 93% female, ZIP `100` = 89% male) combined with lower approval rates in `902` (52%) vs `100` (64.7%) warrants governance attention as a potential *indirect* channel for gender bias.

### 2.4 Interaction Effects

**Gender × Age (most severe segment):**

| Age Group | Female Approval | Male Approval | Segment DI |
|-----------|----------------|---------------|------------|
| 18-30 | **31.1%** | **52.7%** | **0.591** |
| 31-40 | 58.0% | 66.7% | 0.870 |
| 41-50 | 60.0% | 76.9% | 0.781 |
| 51-65 | 51.1% | 63.9% | 0.800 |

**The 18-30 female segment has the most severe disparate impact (DI = 0.591), combining both gender and age bias.**

**Gender × Income:** The gender approval gap persists across all income tertiles (Low/Medium/High), confirming the disparity is *not* explained by income differences alone.

### 2.5 Conditional Fairness (Logistic Regression)

After controlling for `annual_income`, `debt_to_income`, `credit_history_months`, `savings_balance`, and `age`, **gender remains a statistically significant predictor of loan approval** (OR ≈ 0.49, p < 0.001), with a controlled approval gap of approximately −0.16. This indicates the bias is structural - not reducible to differences in financial risk profile.

### 2.6 Bias Type Mapping

| Bias Type | Evidence |
|-----------|----------|
| **Historical bias** | Female-male approval gap likely reflects historical lending patterns encoded in training data |
| **Measurement bias** | Inconsistent gender coding (M/F vs Male/Female) - 22% of records affected |
| **Algorithmic bias** | Gender remains significant after controlling for risk factors |
| **Proxy bias** | ZIP code geography strongly correlates with gender (χ² = 319, p ≈ 0) |
| **Representation bias** | 18-30 age segment underrepresented in approvals relative to risk profile |

## Privacy Assessment

> **Notebook:** `notebooks/03-privacy-demo.ipynb`  
> **Owner:** Amgirus Murali - Governance Officer

### 3.1 PII Inventory

8 PII fields identified across the 498-record dataset:

| Field | PII Type | Risk Level | GDPR Article |
|-------|---------|-----------|-------------|
| `applicant_info.full_name` | Direct PII | High | Art. 4(1) |
| `applicant_info.email` | Direct PII | High | Art. 4(1) |
| `applicant_info.ssn` | Direct PII | **Critical** | Art. 87 |
| `applicant_info.ip_address` | Indirect PII | Medium | Art. 4(1) / Recital 30 |
| `applicant_info.date_of_birth` | Direct PII | High | Art. 4(1) |
| `applicant_info.gender` | Direct PII | High | Art. 4(1) / Art. 9 |
| `applicant_info.zip_code` | Indirect PII | Medium | Art. 4(1) |
| `spending_behavior` | Behavioural PII | High | Art. 5(1)(c) |

**Risk breakdown:** 1 Critical, 5 High, 2 Medium.

### 3.2 Pseudonymization Demonstration

Direct identifiers (`full_name`, `email`, `ssn`, `ip_address`) were pseudonymized using **SHA-256 with a fixed salt** stored separately from the dataset. This is a deterministic pseudonymization scheme - the same input always produces the same hash - enabling linkage by authorized parties while preventing re-identification from the dataset alone.

`date_of_birth` was replaced with **age brackets** (18-30, 31-40, 41-50, 51-65), retaining sufficient granularity for risk modeling and bias monitoring while eliminating the exact quasi-identifier.

### 3.3 GDPR Gap Analysis

All 8 assessed GDPR articles show compliance gaps:

| Article | Gap | Evidence |
|---------|-----|----------|
| Art. 5(1)(a) - Lawful basis | No `consent_timestamp` or `lawful_basis` field in any of 498 records | Dataset |
| Art. 5(1)(c) - Data minimisation | SSN + IP stored raw; granular spending categories with no demonstrated necessity | Dataset |
| Art. 5(1)(d) - Accuracy | 3 SSNs shared across different names; inconsistent gender/date formats | Notebook 01 |
| Art. 5(1)(e) - Storage limitation | No `retention_expiry` or `deletion_timestamp` field | Dataset |
| Art. 13/14 - Transparency | No privacy notice or disclosure field | Dataset |
| Art. 17 - Right to erasure | No `deletion_request_flag` or soft-delete mechanism | Dataset |
| Art. 22 - Automated decisions | 498 automated credit decisions with no `human_review_flag` | Dataset |
| Art. 25 - Privacy by design | PII stored in plaintext; no anonymization at collection | Dataset |

**Potential GDPR fine exposure:** Violations of Art. 5 (Tier 2) carry fines up to €20 million or 4% of global annual turnover (whichever is higher).

### 3.4 EU AI Act Classification

Under **EU AI Act Regulation 2024/1689**, credit scoring systems are explicitly listed in **Annex III, Section 5(b)** as **HIGH-RISK AI systems**.

| Obligation | Article | NovaCred Status |
|-----------|---------|----------------|
| Risk Management System | Art. 9 | MISSING |
| Data Governance documentation | Art. 10 | MISSING |
| Technical Documentation | Art. 11 | MISSING |
| Logging & Audit Trail | Art. 12 | MISSING (87.6% of timestamps absent) |
| Human Oversight | Art. 14 | MISSING (no `human_review_flag`) |
| Accuracy & Robustness | Art. 15 | PARTIAL (bias detected) |

## Governance Recommendations

The following recommendations address the most critical findings, prioritized by urgency and regulatory exposure.

### Immediate (0-3 months)

1. **Add human oversight flag** - Introduce a `human_review_flag` field for all decisions; mandate human review for all rejections and edge cases. Required for EU AI Act Art. 14 compliance.
2. **Pseudonymize PII at collection** - Apply SHA-256 hashing to SSN, name, email, and IP address before storage. Store the salt separately in a secrets manager (e.g. AWS Secrets Manager, Azure Key Vault).
3. **Implement consent tracking** - Add `consent_timestamp` and `consent_version` fields to every application record, and integrate a Consent Management Platform (CMP).
4. **Enforce data type validation at ingestion** - Reject records with mixed-type income fields, non-standard date formats, or ambiguous gender coding at the API gateway level.
5. **Fix SSN uniqueness constraint** - Implement a database-level unique constraint on SSN. Flag SSN conflicts for fraud review rather than silently accepting duplicates.

### Short-term (3-6 months)

6. **Conduct a formal Fairness Audit** - Retrain or audit the ML model using fairness constraints (e.g., demographic parity, equalized odds). The current 18-30 female segment (DI = 0.591) requires immediate model review.
7. **Define and enforce a data retention policy** - Add `retention_expiry` timestamps; delete or archive records older than the defined period (e.g., 5 years for credit data under relevant regulations). Required for Art. 5(1)(e) compliance.
8. **Create a Data Subject Rights API** - Implement endpoints to handle Art. 15 (access), Art. 16 (rectification), Art. 17 (erasure), and Art. 22 (opt-out from automated decisions) requests.
9. **Establish an AI audit trail** - Ensure all model predictions are logged with input features, model version, and timestamp. Currently 87.6% of records lack `processing_timestamp`.

### Strategic (6-12 months)

10. **Develop a Data Governance Framework** - Formalize Data Owner, Data Steward, and Data Custodian roles. The current dataset lacks any governance metadata.
11. **Replace SSN with less-sensitive identifiers** - After identity verification, SSN should be discarded and replaced with an internal applicant ID. SSN storage beyond the identity-check phase is a data minimisation violation.
12. **Aggregate spending behavior** - Replace granular spending categories (Rent, Fitness, Insurance, Gambling, etc.) with broad aggregates unless a specific necessity for each category is documented. Granular behavioral data violates Art. 5(1)(c).
13. **Implement DPIA (Data Protection Impact Assessment)** - Required for high-risk processing under Art. 35 GDPR, triggered by: automated decision-making affecting individuals, profiling using sensitive behavioral data, and large-scale PII processing.
14. **Prepare EU AI Act compliance documentation** - Register the credit scoring model in the EU AI database, produce required Technical Documentation (Art. 11), and establish ongoing monitoring and post-market surveillance.

## How to Run the Notebooks

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn scikit-learn statsmodels
# Optional for Notebook 02:
pip install fairlearn
```

### Execution Order

Notebooks must be run **in order** - each notebook builds on the output of the previous:

```
01-data-quality.ipynb  →  produces: data/credit_applications_clean_final.csv
02-bias-analysis.ipynb →  reads:    data/credit_applications_clean_final.csv
03-privacy-demo.ipynb  →  reads:    data/credit_applications_clean_final.csv
```


## Presentation

**Video (Group 14):** [https://youtu.be/wUUoNP9x1sI](https://youtu.be/wUUoNP9x1sI)

## Technologies Used

| Library | Purpose |
|---------|---------|
| `pandas` | Data loading, cleaning, aggregation |
| `numpy` | Numerical operations |
| `matplotlib` / `seaborn` | Visualisations |
| `scipy` | Chi-square tests, t-tests, statistical testing |
| `statsmodels` | Logistic regression (conditional fairness) |
| `fairlearn` | Demographic parity difference (optional; fallback implemented if not installed) |

## Key Takeaways

- **Data quality must be addressed before and alongside fairness and privacy work.** Duplicates, missing timestamps, inconsistent encodings, and invalid values affect both model behaviour and auditability.

- **Gender disparate impact (DI = 0.767) and conditional unfairness after controlling for risk** (OR ≈ 0.49, p < 0.001) indicate the current lending process poses fairness and regulatory risk. Segment-level analysis shows young women aged 18-30 are the most disadvantaged subgroup (DI = 0.591).

- **PII is stored in plain text without adequate consent, retention, or erasure mechanisms.** Pseudonymisation (salted SHA-256 hashing, age bracketing) and lifecycle controls are needed to meet GDPR and reduce breach risk.

- **Credit scoring is high-risk under the EU AI Act (Annex III, Section 5(b)).** NovaCred must implement data governance, human oversight, bias monitoring, and conformity assessment before the system can be treated as compliant for automated deployment.

- **The recommended governance controls** (audit trails, human oversight, retention policies, consent tracking, right-to-erasure workflows, bias monitoring, and secure PII handling) form a concrete roadmap to align with responsible lending, GDPR, and the EU AI Act.

*Version 1.0 | DEGO 2606 - Data Ecosystems and Governance in Organizations | Nova SBE*
