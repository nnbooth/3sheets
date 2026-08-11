#!/usr/bin/env python3
"""Generate the CSV source-of-truth for the legal finance dataset.

Quick summary:
- This script creates and refreshes synthetic data rows.
- Output is CSV files in Legal/data (dimensions + fact tables).
- It does not create PostgreSQL views.

The reporting model is transaction-driven:
- client and matter dimensions
- work performed at the timecard level
- billing rows linked back to each timecard
- disbursements as separate matter-level transactions
- fee-earner budgets by calendar month

There is no standalone monthly WIP fact table. WIP is derived from work,
billing, and write-offs using ledger dates.
"""

from __future__ import annotations

import csv
import hashlib
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LEGAL_DIR = SCRIPT_DIR.parent
DATA_DIR = LEGAL_DIR / "data"

CLIENT_PATH = DATA_DIR / "dim_client.csv"
MATTER_PATH = DATA_DIR / "dim_matter.csv"
F_MATTER_PATH = DATA_DIR / "fact_matter.csv"
OFFICE_PATH = DATA_DIR / "dim_office_location.csv"
WORK_PATH = DATA_DIR / "fact_work_performed.csv"
BILLING_PATH = DATA_DIR / "fact_billing.csv"
DISB_PATH = DATA_DIR / "fact_disbursements.csv"
BUDGET_PATH = DATA_DIR / "fact_fee_earner_budget_monthly.csv"
DATE_PATH = DATA_DIR / "dim_date.csv"

WORK_NARRATIVES = [
    "Client call",
    "File review",
    "Draft letter",
    "Court prep",
    "Research note",
    "Settlement call",
    "Prepare brief",
    "Review evidence",
    "Amend docs",
    "Draft statement",
    "Discovery review",
    "Draft note",
    "Case planning",
    "Advise client",
    "Prepare submission",
]

DISB_NARRATIVES = [
    "Court filing",
    "Medical records",
    "Search fee",
    "Barrister fee",
    "Expert report",
    "Service fee",
    "Mediation fee",
    "Transcript fee",
    "Records request",
]

CLIENT_SEGMENTS = ["Individual", "Small Business", "Corporate", "Insurer"]
MAX_LEDGER_DATE = date(2027, 2, 28)
WORK_GENERATION_END = date(2026, 12, 31)

OFFICE_LOCATIONS = [
    {"office_id": 1, "office_name": "Brisbane CBD", "city": "Brisbane", "state": "Queensland", "postcode": "4000", "country": "Australia", "latitude": -27.4698, "longitude": 153.0251},
    {"office_id": 2, "office_name": "Gold Coast", "city": "Southport", "state": "Queensland", "postcode": "4215", "country": "Australia", "latitude": -27.9679, "longitude": 153.3970},
    {"office_id": 3, "office_name": "Sunshine Coast", "city": "Maroochydore", "state": "Queensland", "postcode": "4558", "country": "Australia", "latitude": -26.6500, "longitude": 153.0667},
    {"office_id": 4, "office_name": "Townsville", "city": "Townsville", "state": "Queensland", "postcode": "4810", "country": "Australia", "latitude": -19.2589, "longitude": 146.8169},
    {"office_id": 5, "office_name": "Cairns", "city": "Cairns", "state": "Queensland", "postcode": "4870", "country": "Australia", "latitude": -16.9186, "longitude": 145.7781},
    {"office_id": 6, "office_name": "Sydney CBD", "city": "Sydney", "state": "New South Wales", "postcode": "2000", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093},
    {"office_id": 7, "office_name": "Parramatta", "city": "Parramatta", "state": "New South Wales", "postcode": "2150", "country": "Australia", "latitude": -33.8150, "longitude": 151.0011},
    {"office_id": 8, "office_name": "Melbourne CBD", "city": "Melbourne", "state": "Victoria", "postcode": "3000", "country": "Australia", "latitude": -37.8136, "longitude": 144.9631},
]

# Heavily weighted towards Queensland with some NSW and VIC representation.
OFFICE_WEIGHT_IDS = [1, 1, 1, 2, 2, 3, 4, 5, 1, 2, 6, 7, 8]


def truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


def easter_sunday(year: int) -> date:
    # Anonymous Gregorian algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def observed_if_weekend(dt: date) -> date:
    if dt.weekday() == 5:
        return dt + timedelta(days=2)
    if dt.weekday() == 6:
        return dt + timedelta(days=1)
    return dt


def first_weekday_of_month(year: int, month: int, weekday: int) -> date:
    d = date(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def is_obvious_au_public_holiday(dt: date) -> bool:
    year = dt.year
    easter = easter_sunday(year)

    new_year = observed_if_weekend(date(year, 1, 1))
    australia_day = observed_if_weekend(date(year, 1, 26))
    good_friday = easter - timedelta(days=2)
    easter_monday = easter + timedelta(days=1)
    anzac_day = date(year, 4, 25)
    labour_day_qld = first_weekday_of_month(year, 5, 0)  # first Monday in May
    kings_birthday_qld = first_weekday_of_month(year, 10, 0)  # first Monday in Oct
    christmas_day = observed_if_weekend(date(year, 12, 25))
    boxing_day = observed_if_weekend(date(year, 12, 26))

    holidays = {
        new_year,
        australia_day,
        good_friday,
        easter_monday,
        anzac_day,
        labour_day_qld,
        kings_birthday_qld,
        christmas_day,
        boxing_day,
    }
    return dt in holidays


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts)
    digest = hashlib.blake2b(payload.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def month_start(dt: date) -> date:
    return date(dt.year, dt.month, 1)


def add_months(year: int, month: int, offset: int) -> tuple[int, int]:
    total = (year * 12 + month - 1) + offset
    return total // 12, total % 12 + 1


def month_range(start: date, end: date) -> list[tuple[int, int]]:
    current_year, current_month = start.year, start.month
    end_year, end_month = end.year, end.month
    months: list[tuple[int, int]] = []
    while (current_year, current_month) <= (end_year, end_month):
        months.append((current_year, current_month))
        current_year, current_month = add_months(current_year, current_month, 1)
    return months


def extend_dim_date(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    last_date = parse_date(rows[-1]["date"])
    if last_date is None:
        return rows
    current = last_date + timedelta(days=1)
    while current <= MAX_LEDGER_DATE:
        rows.append(
            {
                "date": current.isoformat(),
                "year": str(current.year),
                "month": str(current.month),
                "month_name": current.strftime("%b"),
                "quarter": str(((current.month - 1) // 3) + 1),
                "day_of_week": current.strftime("%A"),
                "is_weekend": str(1 if current.weekday() >= 5 else 0),
                "financial_year": f"FY{current.year + 1 if current.month >= 7 else current.year}",
                "is_court_vacation": str(1 if current.month in (12, 1) else 0),
            }
        )
        current += timedelta(days=1)
    return rows


def workdays_by_month(dim_date_rows: list[dict[str, str]]) -> dict[tuple[int, int], list[str]]:
    grouped: dict[tuple[int, int], list[str]] = defaultdict(list)
    for row in dim_date_rows:
        dt = parse_date(row["date"])
        if dt is None:
            continue
        if truthy(row.get("is_weekend")) or truthy(row.get("is_court_vacation")):
            continue
        if is_obvious_au_public_holiday(dt):
            continue
        grouped[(int(row["year"]), int(row["month"]))].append(row["date"])
    for values in grouped.values():
        values.sort()
    return grouped


def build_dim_client(matter_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    clients: list[dict[str, object]] = []
    seen: set[int] = set()
    for matter in matter_rows:
        matter_id = int(matter["matter_id"])
        client_id = ((matter_id - 1) // 4) + 1
        if client_id in seen:
            continue
        seen.add(client_id)
        clients.append(
            {
                "client_id": client_id,
                "client_name": f"Client {client_id:04d}",
                "client_segment": CLIENT_SEGMENTS[(client_id - 1) % len(CLIENT_SEGMENTS)],
            }
        )
    clients.sort(key=lambda row: int(row["client_id"]))
    return clients


def build_dim_matter(
    matter_rows: list[dict[str, str]],
    practice_lookup: dict[int, dict[str, str]],
    fee_earners: dict[int, dict[str, str]],
) -> list[dict[str, object]]:
    matters: list[dict[str, object]] = []
    for row in matter_rows:
        matter_id = int(row["matter_id"])
        practice_area_id = int(row["practice_area_id"])
        fee_earner_id = int(row["fee_earner_id"])
        fee_earner = fee_earners[fee_earner_id]
        client_id = ((matter_id - 1) // 4) + 1
        matters.append(
            {
                "matter_id": matter_id,
                "client_id": client_id,
                "matter_reference": f"MAT-{matter_id:05d}",
                "matter_name": f"Matter {matter_id:05d}",
                "practice_area_id": practice_area_id,
                "practice_area_name": practice_lookup[practice_area_id]["practice_area_name"],
                "fee_earner_id": fee_earner_id,
                "referral_source_id": int(row["referral_source_id"]),
                "office_id": int(fee_earner["office_id"]),
                "office_name": fee_earner["office_name"],
                "city": fee_earner["city"],
                "state": fee_earner["state"],
                "postcode": fee_earner["postcode"],
                "country": fee_earner["country"],
                "open_date": row["open_date"],
                "close_date": row["close_date"],
                "status": row["status"],
                "fee_type": row["fee_type"],
            }
        )
    return matters


def build_dim_office_location() -> list[dict[str, object]]:
    return [dict(row) for row in OFFICE_LOCATIONS]


def enrich_fee_earners_with_office(
    fee_earner_rows: list[dict[str, str]],
    office_lookup: dict[int, dict[str, object]],
) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for row in fee_earner_rows:
        fee_earner_id = int(row["fee_earner_id"])
        office_idx = stable_seed("office", fee_earner_id) % len(OFFICE_WEIGHT_IDS)
        office_id = OFFICE_WEIGHT_IDS[office_idx]
        office = office_lookup[office_id]
        enriched.append(
            {
                **row,
                "office_id": office_id,
                "office_name": office["office_name"],
                "city": office["city"],
                "state": office["state"],
                "postcode": office["postcode"],
                "country": office["country"],
                "latitude": office["latitude"],
                "longitude": office["longitude"],
            }
        )
    return enriched


def build_budget_rows(
    fee_earners: dict[int, dict[str, str]],
    dim_date_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    workday_counts: dict[tuple[int, int], int] = defaultdict(int)
    month_names: dict[tuple[int, int], str] = {}
    financial_years: dict[tuple[int, int], str] = {}
    for row in dim_date_rows:
        dt = parse_date(row["date"])
        if dt is None:
            continue
        if truthy(row.get("is_weekend")) or truthy(row.get("is_court_vacation")):
            continue
        if is_obvious_au_public_holiday(dt):
            continue
        key = (int(row["year"]), int(row["month"]))
        workday_counts[key] += 1
        month_names[key] = row["month_name"]
        financial_years[key] = row["financial_year"]

    rows: list[dict[str, object]] = []
    budget_id = 1
    for fee_earner_id, fe in sorted(fee_earners.items()):
        practice_area_id = int(fe["primary_practice_area_id"])
        hourly_rate = float(fe["hourly_rate"])
        for (year, month) in sorted(workday_counts):
            workdays = workday_counts[(year, month)]
            budget_hours = round(workdays * 6.0, 2)
            rows.append(
                {
                    "budget_id": budget_id,
                    "fee_earner_id": fee_earner_id,
                    "office_id": int(fe["office_id"]),
                    "office_name": fe["office_name"],
                    "city": fe["city"],
                    "state": fe["state"],
                    "postcode": fe["postcode"],
                    "country": fe["country"],
                    "practice_area_id": practice_area_id,
                    "year": year,
                    "month": month,
                    "month_name": month_names[(year, month)],
                    "financial_year": financial_years[(year, month)],
                    "workdays_in_month": workdays,
                    "budget_hours": budget_hours,
                    "budget_revenue": round(budget_hours * hourly_rate, 2),
                }
            )
            budget_id += 1
    return rows


def month_lag_for_status(status: str) -> tuple[int, int]:
    if status == "Settled":
        return 7, 20
    if status.startswith("Trial"):
        return 10, 30
    if status == "Discontinued":
        return 15, 40
    return 10, 45


def build_transaction_rows(
    matter_rows: list[dict[str, str]],
    fee_earners: dict[int, dict[str, str]],
    workdays: dict[tuple[int, int], list[str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    matter_lookup = {int(row["matter_id"]): row for row in matter_rows}
    work_rows: list[dict[str, object]] = []
    billing_rows: list[dict[str, object]] = []
    disb_rows: list[dict[str, object]] = []

    timecard_id = 1
    billing_id = 1
    disb_id = 1

    for matter_id in sorted(matter_lookup):
        matter = matter_lookup[matter_id]
        fee_earner_id = int(matter["fee_earner_id"])
        fee_earner = fee_earners[fee_earner_id]
        office_id = int(fee_earner["office_id"])
        office_name = fee_earner["office_name"]
        office_city = fee_earner["city"]
        office_state = fee_earner["state"]
        office_postcode = fee_earner["postcode"]
        office_country = fee_earner["country"]
        hourly_rate = float(fee_earner["hourly_rate"])
        practice_area_id = int(matter["practice_area_id"])
        matter_open = parse_date(matter["open_date"])
        matter_close = parse_date(matter["close_date"]) or WORK_GENERATION_END
        work_end = min(matter_close, WORK_GENERATION_END)
        active_months = [
            (year, month)
            for year, month in month_range(matter_open or work_end, work_end)
            if workdays.get((year, month))
        ]
        if not active_months:
            active_months = [(work_end.year, work_end.month)]

        total_bill = float(matter["legal_fees_billed"])
        total_writeoff = float(matter["write_off_amount"])
        total_work_value = total_bill + total_writeoff
        total_hours = max(0.5, round(total_work_value / hourly_rate, 2))

        seed = stable_seed("matter", matter_id)
        rng = random.Random(seed)
        month_weights = [0.75 + rng.random() for _ in active_months]
        month_weight_sum = sum(month_weights) or 1.0
        month_hours = [round(total_hours * weight / month_weight_sum, 2) for weight in month_weights[:-1]]
        month_hours.append(round(total_hours - sum(month_hours), 2))

        timecards: list[dict[str, object]] = []
        for (year, month), hours_for_month in zip(active_months, month_hours):
            valid_days = workdays[(year, month)]
            min_cards = 2 if total_bill > 0 and total_writeoff > 0 else 1
            card_count = max(min_cards, min(6, int(round(hours_for_month / 4.0))))
            card_weights = [rng.random() for _ in range(card_count)]
            card_weight_sum = sum(card_weights) or 1.0
            card_hours = [round(hours_for_month * weight / card_weight_sum, 2) for weight in card_weights[:-1]]
            card_hours.append(round(hours_for_month - sum(card_hours), 2))
            picked_days = [valid_days[min(i, len(valid_days) - 1)] for i in range(card_count)]
            rng.shuffle(picked_days)
            for hours, work_date in zip(card_hours, picked_days):
                narrative = rng.choice(WORK_NARRATIVES)
                work_rows.append(
                    {
                        "timecard_id": timecard_id,
                        "matter_id": matter_id,
                        "work_date": work_date,
                        "ledger_date": work_date,
                        "fee_earner_id": fee_earner_id,
                        "office_id": office_id,
                        "office_name": office_name,
                        "city": office_city,
                        "state": office_state,
                        "postcode": office_postcode,
                        "country": office_country,
                        "hours_worked": round(hours, 2),
                        "work_value_generated": round(hours * hourly_rate, 2),
                        "narrative": narrative,
                    }
                )
                timecards.append(
                    {
                        "timecard_id": timecard_id,
                        "matter_id": matter_id,
                        "work_date": work_date,
                        "ledger_date": work_date,
                        "fee_earner_id": fee_earner_id,
                        "practice_area_id": practice_area_id,
                        "hours_worked": round(hours, 2),
                        "work_value_generated": round(hours * hourly_rate, 2),
                        "narrative": narrative,
                    }
                )
                timecard_id += 1

        billed_share = total_bill / total_work_value if total_work_value else 1.0
        writeoff_share = total_writeoff / total_work_value if total_work_value else 0.0
        billed_card_ids: list[int] = []
        writeoff_card_ids: list[int] = []

        for card in timecards:
            if total_writeoff > 0 and total_bill > 0:
                choose_writeoff = rng.random() < writeoff_share
            else:
                choose_writeoff = total_bill <= 0
            if choose_writeoff:
                writeoff_card_ids.append(card["timecard_id"])
            else:
                billed_card_ids.append(card["timecard_id"])

        if total_bill > 0 and not billed_card_ids:
            billed_card_ids.append(writeoff_card_ids.pop())
        if total_writeoff > 0 and not writeoff_card_ids and billed_card_ids:
            writeoff_card_ids.append(billed_card_ids.pop())

        billed_timecards = [card for card in timecards if card["timecard_id"] in billed_card_ids]
        writeoff_timecards = [card for card in timecards if card["timecard_id"] in writeoff_card_ids]

        billed_hours_total = sum(card["hours_worked"] for card in billed_timecards) or 1.0
        writeoff_hours_total = sum(card["hours_worked"] for card in writeoff_timecards) or 1.0
        billed_lag_min, billed_lag_max = month_lag_for_status(matter["status"])
        writeoff_lag_min, writeoff_lag_max = billed_lag_min + 10, billed_lag_max

        for card in billed_timecards:
            share = card["hours_worked"] / billed_hours_total
            billed_amount = round(total_bill * share, 2)
            billing_date = min(
                MAX_LEDGER_DATE,
                parse_date(card["work_date"]) + timedelta(days=rng.randint(billed_lag_min, billed_lag_max)),
            )
            billing_rows.append(
                {
                    "billing_id": billing_id,
                    "timecard_id": card["timecard_id"],
                    "matter_id": matter_id,
                    "billing_date": billing_date.isoformat(),
                    "ledger_date": billing_date.isoformat(),
                    "invoice_number": f"INV-{matter_id:05d}-{billing_date:%Y%m}",
                    "fee_earner_id": fee_earner_id,
                    "office_id": office_id,
                    "office_name": office_name,
                    "city": office_city,
                    "state": office_state,
                    "postcode": office_postcode,
                    "country": office_country,
                    "billed_hours": card["hours_worked"],
                    "billed_rate": hourly_rate,
                    "billed_amount": billed_amount,
                    "writeoff_amount": 0.0,
                    "billing_status": "Billed",
                    "billing_narrative": card["narrative"],
                }
            )
            billing_id += 1

        for card in writeoff_timecards:
            share = card["hours_worked"] / writeoff_hours_total
            writeoff_amount = round(total_writeoff * share, 2)
            billing_date = min(
                MAX_LEDGER_DATE,
                parse_date(card["work_date"]) + timedelta(days=rng.randint(writeoff_lag_min, writeoff_lag_max)),
            )
            billing_rows.append(
                {
                    "billing_id": billing_id,
                    "timecard_id": card["timecard_id"],
                    "matter_id": matter_id,
                    "billing_date": billing_date.isoformat(),
                    "ledger_date": billing_date.isoformat(),
                    "invoice_number": "writeoff_date",
                    "fee_earner_id": fee_earner_id,
                    "office_id": office_id,
                    "office_name": office_name,
                    "city": office_city,
                    "state": office_state,
                    "postcode": office_postcode,
                    "country": office_country,
                    "billed_hours": 0.0,
                    "billed_rate": hourly_rate,
                    "billed_amount": 0.0,
                    "writeoff_amount": writeoff_amount,
                    "billing_status": "Written Off",
                    "billing_narrative": card["narrative"],
                }
            )
            billing_id += 1

        disb_target = float(matter["disbursements_paid"])
        if disb_target > 0:
            disb_seed = random.Random(stable_seed("disb", matter_id))
            disb_count = max(1, min(3, int(round(disb_target / 750.0)) or 1))
            disb_weights = [disb_seed.random() for _ in range(disb_count)]
            disb_weight_sum = sum(disb_weights) or 1.0
            disb_amounts = [round(disb_target * weight / disb_weight_sum, 2) for weight in disb_weights[:-1]]
            disb_amounts.append(round(disb_target - sum(disb_amounts), 2))
            open_dt = matter_open or parse_date(matter["open_date"]) or date(2026, 1, 1)
            close_dt = parse_date(matter["close_date"]) or MAX_LEDGER_DATE
            span_days = max(0, (close_dt - open_dt).days)
            for index, amount in enumerate(disb_amounts, start=1):
                if amount <= 0:
                    continue
                event_date = open_dt + timedelta(days=min(span_days, int(span_days * index / (disb_count + 1))))
                event_date = min(event_date, MAX_LEDGER_DATE)
                disb_rows.append(
                    {
                        "disbursement_id": disb_id,
                        "matter_id": matter_id,
                        "office_id": office_id,
                        "office_name": office_name,
                        "city": office_city,
                        "state": office_state,
                        "postcode": office_postcode,
                        "country": office_country,
                        "disbursement_date": event_date.isoformat(),
                        "ledger_date": event_date.isoformat(),
                        "invoice_number": f"DISB-{matter_id:05d}-{index:02d}",
                        "disbursement_narrative": disb_seed.choice(DISB_NARRATIVES),
                        "disbursement_amount": amount,
                    }
                )
                disb_id += 1

    return work_rows, billing_rows, disb_rows


def main() -> None:
    dim_date_rows = extend_dim_date(read_csv(DATE_PATH))
    fee_earner_rows = read_csv(DATA_DIR / "dim_fee_earner.csv")
    practice_rows = read_csv(DATA_DIR / "dim_practice_area.csv")
    matter_rows = read_csv(F_MATTER_PATH)

    office_rows = build_dim_office_location()
    office_lookup = {int(row["office_id"]): row for row in office_rows}
    fee_earner_rows = enrich_fee_earners_with_office(fee_earner_rows, office_lookup)

    fee_earners = {int(row["fee_earner_id"]): row for row in fee_earner_rows}
    practices = {int(row["practice_area_id"]): row for row in practice_rows}
    workdays = workdays_by_month(dim_date_rows)

    dim_client_rows = build_dim_client(matter_rows)
    dim_matter_rows = build_dim_matter(matter_rows, practices, fee_earners)
    fact_work_rows, fact_billing_rows, fact_disb_rows = build_transaction_rows(matter_rows, fee_earners, workdays)
    budget_rows = build_budget_rows(fee_earners, dim_date_rows)

    fact_matter_rows: list[dict[str, object]] = []
    for row in matter_rows:
        fee_earner = fee_earners[int(row["fee_earner_id"])]
        fact_matter_rows.append(
            {
                **row,
                "office_id": int(fee_earner["office_id"]),
                "office_name": fee_earner["office_name"],
                "city": fee_earner["city"],
                "state": fee_earner["state"],
                "postcode": fee_earner["postcode"],
                "country": fee_earner["country"],
            }
        )

    write_csv(DATE_PATH, dim_date_rows, [
        "date", "year", "month", "month_name", "quarter", "day_of_week", "is_weekend", "financial_year", "is_court_vacation",
    ])
    write_csv(OFFICE_PATH, office_rows, [
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "latitude",
        "longitude",
    ])
    write_csv(DATA_DIR / "dim_fee_earner.csv", fee_earner_rows, [
        "fee_earner_id",
        "name",
        "role",
        "primary_practice_area_id",
        "hourly_rate",
        "target_utilization_pct",
        "start_date",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "latitude",
        "longitude",
    ])
    write_csv(CLIENT_PATH, dim_client_rows, ["client_id", "client_name", "client_segment"])
    write_csv(F_MATTER_PATH, fact_matter_rows, [
        "matter_id",
        "practice_area_id",
        "fee_earner_id",
        "referral_source_id",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "open_date",
        "close_date",
        "status",
        "fee_type",
        "estimated_claim_value",
        "settlement_value",
        "legal_fees_billed",
        "disbursements_paid",
        "amount_collected",
        "write_off_amount",
    ])
    write_csv(MATTER_PATH, dim_matter_rows, [
        "matter_id",
        "client_id",
        "matter_reference",
        "matter_name",
        "practice_area_id",
        "practice_area_name",
        "fee_earner_id",
        "referral_source_id",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "open_date",
        "close_date",
        "status",
        "fee_type",
    ])
    write_csv(WORK_PATH, fact_work_rows, [
        "timecard_id",
        "matter_id",
        "work_date",
        "ledger_date",
        "fee_earner_id",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "hours_worked",
        "work_value_generated",
        "narrative",
    ])
    write_csv(BILLING_PATH, fact_billing_rows, [
        "billing_id",
        "timecard_id",
        "matter_id",
        "billing_date",
        "ledger_date",
        "invoice_number",
        "fee_earner_id",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "billed_hours",
        "billed_rate",
        "billed_amount",
        "writeoff_amount",
        "billing_status",
        "billing_narrative",
    ])
    write_csv(DISB_PATH, fact_disb_rows, [
        "disbursement_id",
        "matter_id",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "disbursement_date",
        "ledger_date",
        "invoice_number",
        "disbursement_narrative",
        "disbursement_amount",
    ])
    write_csv(BUDGET_PATH, budget_rows, [
        "budget_id",
        "fee_earner_id",
        "office_id",
        "office_name",
        "city",
        "state",
        "postcode",
        "country",
        "practice_area_id",
        "year",
        "month",
        "month_name",
        "financial_year",
        "workdays_in_month",
        "budget_hours",
        "budget_revenue",
    ])

    legacy_wip = DATA_DIR / ("fact" + "_wip_monthly.csv")
    if legacy_wip.exists():
        legacy_wip.unlink()

    print(f"Wrote {DATE_PATH.name} through {dim_date_rows[-1]['date']}")
    print(f"Wrote {CLIENT_PATH.name} with {len(dim_client_rows):,} rows")
    print(f"Wrote {MATTER_PATH.name} with {len(dim_matter_rows):,} rows")
    print(f"Wrote {WORK_PATH.name} with {len(fact_work_rows):,} rows")
    print(f"Wrote {BILLING_PATH.name} with {len(fact_billing_rows):,} rows")
    print(f"Wrote {DISB_PATH.name} with {len(fact_disb_rows):,} rows")
    print(f"Wrote {BUDGET_PATH.name} with {len(budget_rows):,} rows")
    print("Removed obsolete WIP CSV" if not legacy_wip.exists() else "Obsolete WIP CSV still present")


if __name__ == "__main__":
    main()
