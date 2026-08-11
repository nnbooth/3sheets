# Clinic Operations Dataset — for Looker Studio

Synthetic allied health clinic dataset, Jan 2023 – Jun 2026 (Australian context: Medicare
rebates, bulk billing, DVA). Clinic grows from 4 to ~10 providers across the period, mirroring
a scaling practice.

## Repository Location

This dataset is stored at `datasets/Health/data/` in the DataPortfolio repository.

## Schema

```
dim_provider ------\
dim_service_type ----> fact_appointments (1 row per booking)
dim_date -----------------> fact_claims (1 row per billable attended appointment)
```

**dim_provider** — provider_id, name, specialty (GP/Physio/Psychologist/Dietitian/Exercise
Physiologist/Podiatrist), start_date, end_date (null if still active), fte,
standard_appointment_length_min

**dim_service_type** — service_type_id, service_name, mbs_item_number, standard_fee,
medicare_rebate

**dim_date** — date, year, month, quarter, day_of_week, is_weekend, financial_year

**fact_appointments** — appointment_id, date, provider_id, service_type_id, patient_id
(synthetic ID, no PII), status (Attended/No-show/Cancelled), booking_date, wait_days,
billing_type (Bulk Billed/Private/DVA), fee_charged, medicare_rebate_amount,
patient_out_of_pocket, patient_satisfaction_score (1–5, attended only)

**fact_claims** — claim_id, appointment_id, submission_date, claim_amount, claim_status
(Paid/Rejected/Pending), payment_date, rejection_reason

Join `fact_claims.appointment_id` → `fact_appointments.appointment_id`. Join provider/service
dimensions directly onto `fact_appointments`.

## Insights baked into the data (verified)

1. **Bulk billing decline**: bulk-billed share of appointments falls from ~70% (2023) to ~46%
   (2026 YTD) — rising patient out-of-pocket costs over time, a real trend in AU primary care.
2. **Wait time → no-show correlation**: no-show rate climbs from ~5% (booked within 3 days) to
   ~28% (booked 30+ days out) — a clear scheduling/capacity story.
3. **Claims rejection spike**: rejection rate jumps from ~4–5% baseline to ~18% for Jul–Sep 2024
   (a simulated claims-system migration), then recovers — good for a root-cause/process chart.
4. **Clinic growth**: provider headcount grows from 4 to ~10 over the period; one physio departs
   in late 2024 (staff turnover).
5. **Provider capacity constraint**: Psychologist appointments carry longer average wait times
   than other specialties by design.

## Suggested Looker Studio calculated fields / charts

- No-show rate by wait_days bucket (scorecard + bar chart)
- Bulk billed % trend, monthly, with a reference line at clinic average
- Claims rejection rate trend, monthly (spike visible Jul–Sep 2024)
- Average wait_days by provider/specialty
- Patient satisfaction trend vs wait_days (scatter or dual-axis)
- Revenue mix: Medicare rebate vs patient out-of-pocket, by billing_type over time

## Notes

All providers, patients, and appointments are synthetic — no real clinic, clinician, or patient
data. MBS item numbers and rebate amounts are illustrative, not current schedule fees. Amounts
in AUD.

Recommended file loading order:

1. `dim_date.csv`
2. `dim_provider.csv`
3. `dim_service_type.csv`
4. `fact_appointments.csv`
5. `fact_claims.csv`
