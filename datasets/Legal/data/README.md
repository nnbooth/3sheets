# Legal / Insurance Finance Dataset

Synthetic personal injury law firm dataset, Jan 2023 – Feb 2027 (QLD-flavoured: CTP, WorkCover,
TPD). Built as a transaction-led star schema with separate client and matter dimensions plus fact
tables for work performed, billing, disbursements, and fee-earner budgets.

## Repository Location

This dataset is stored at `datasets/Legal/data/` in the DataPortfolio repository.

## Current storage / migration status

- PostgreSQL is the runtime for ingestion and reporting models.
- Keep dimensional and fact table names stable when updating loaders or views.
- Reporting intent remains unchanged even as tools are swapped (Power BI, Looker Studio, exports).
- Loader and model scripts for this dataset live in `datasets/Legal/scripts/`.

## Schema

```
dim_client -------------\
                         -> dim_matter ----\
dim_practice_area ------/                   \
dim_fee_earner ---------\                    -> fact_work_performed (1 row per timecard)
dim_referral_source -----\                  / -> fact_billing (1 row per billed or written-off timecard)
dim_date -----------------\                /  -> fact_disbursements (line items by matter)
                                                   -> fact_fee_earner_budget_monthly (1 row per fee earner per month)
```

**dim_client** — client_id, client_name, client_segment
**dim_matter** — matter_id, client_id, matter_reference, matter_name, practice_area_id, practice_area_name,
fee_earner_id, referral_source_id, open_date, close_date, status, fee_type
**dim_practice_area** — practice_area_id, practice_area_name, avg_duration_months, nwnf_share
**dim_fee_earner** — fee_earner_id, name, role, primary_practice_area_id, hourly_rate, target_utilization_pct, start_date
**dim_referral_source** — referral_source_id, source_name, quality_factor
**dim_date** — date, year, month, quarter, day_of_week, is_weekend, financial_year (AU, Jul–Jun), is_court_vacation

**fact_matter** — matter_id, practice_area_id, fee_earner_id, referral_source_id, open_date,
close_date (null if still open), status (Open/Settled/Discontinued/Trial - Won/Trial - Lost),
fee_type (No Win No Fee/Hourly), estimated_claim_value, settlement_value, legal_fees_billed,
disbursements_paid, amount_collected, write_off_amount

**fact_work_performed** — timecard_id, matter_id, work_date, ledger_date, fee_earner_id,
office/location fields, hours_worked, work_value_generated, narrative

**fact_billing** — billing_id, timecard_id, matter_id, billing_date, ledger_date, invoice_number,
fee_earner_id, office/location fields, billed_hours, billed_rate, billed_amount, writeoff_amount,
billing_status, billing_narrative

**fact_disbursements** — disbursement_id, matter_id, disbursement_date, ledger_date, invoice_number,
office/location fields, disbursement_narrative, disbursement_amount

**fact_fee_earner_budget_monthly** — budget_id, fee_earner_id, practice_area_id, year, month,
month_name, financial_year, workdays_in_month, budget_hours, budget_revenue

Join `fact_work_performed.timecard_id` → `fact_billing.timecard_id` to tie work done to invoices.
Join `fact_work_performed.matter_id` → `dim_matter.matter_id` to bring client and matter names onto
time-based reporting. Use ledger dates in the transaction tables to compute point-in-time WIP as
work performed less billed amounts less write-offs.

## Insights baked into the data (verified)

1. **Realization rate gap**: No Win No Fee matters collect less of their work value than hourly
   matters, so write-off exposure is concentrated in NWNF.
2. **Matter WIP aging**: Medical Negligence matters tend to carry the longest outstanding ledger
   balances because the work is performed well before the billing or write-off ledger date.
3. **Referral source quality**: Referral Partner Network and insurer-style referrals convert to
   higher settlement values than paid channels — a source-quality story for a marketing dashboard.
4. **Seasonality**: matter volume drops sharply in Dec/Jan (court vacation) and spikes in June
   (EOFY billing push).
5. **Growth trend**: ~14%/yr matter volume growth baked into the transaction generation.

## Suggested reporting questions / dashboard

- Top fee earners by department, ranked by work performed hours
- Fee earners vs budget by calendar month
- Matter recoverability by timecard and by matter, using ledger dates
- WIP balance as-of a ledger date, derived from work less billing less write-offs
- Settlement value distribution by referral source
- EOFY cohort: matters opened/closed in June vs other months

## Notes

All names, matters, and financials are synthetic — no real clients, firms, or individuals.
Amounts in AUD.
