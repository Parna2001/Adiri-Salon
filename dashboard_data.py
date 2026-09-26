"""Build dashboard_data.json for dashboard.html from the salon customer Excel file.

Usage:
    python dashboard_data.py                      # uses the Excel file next to this script
    python dashboard_data.py --input other.xlsx   # a different workbook
    python dashboard_data.py --today 2026-09-26   # pretend it is another day (testing)

Re-run it whenever the Excel file changes. It also writes dashboard_data.js, a copy of the same data
that dashboard.html loads so the dashboard opens with a plain double-click (see README_SALON_DASHBOARD.md).
Both generated files hold real customer details and are git-ignored.
"""

import argparse
import calendar
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUTPUT_JSON = HERE / "dashboard_data.json"
OUTPUT_JS = HERE / "dashboard_data.js"

MONTHS = list(calendar.month_name)[1:]  # January..December
MONTH_LOOKUP = {}
for _i, _name in enumerate(MONTHS, start=1):
    MONTH_LOOKUP[_name.lower()] = _i
    MONTH_LOOKUP[_name[:3].lower()] = _i
MONTH_LOOKUP["sept"] = 9

# The "Date of Entry" column mixes text dates (M/D/YYYY) with real Excel dates. The real Excel dates
# were parsed as D/M/YYYY when typed, so day and month are swapped (e.g. 11/10/2024 typed as Nov 10
# became 2024-10-11). Row order confirms it: swapped values slot in between their neighbours.
SWAP_EXCEL_DATE_DAY_MONTH = True

FIELDS = [
    ("First_Name", "First name"),
    ("Last_Name", "Last name"),
    ("Mobile_1", "Mobile 1"),
    ("Mobile_2", "Mobile 2"),
    ("Birth_Day", "Birth day"),
    ("Birth_Month", "Birth month"),
    ("Anniversary_Day", "Anniversary day"),
    ("Anniversary_Month", "Anniversary month"),
    ("Date of Entry", "Date of entry"),
]


def blank(v):
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""


def clean_text(v):
    if blank(v):
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s.title() if s.islower() or s.isupper() else s


def clean_mobile(v):
    """Digits only, as a string. Drops a +91 / 0 prefix. Returns None if blank."""
    if blank(v):
        return None
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    digits = re.sub(r"\D", "", str(v))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits or None


def mobile_is_valid(digits):
    return bool(digits) and len(digits) == 10 and digits[0] in "6789"


def clean_month(v):
    """'june', 'Jun', 'JUNE', 6 -> 6. Returns None if blank or unrecognised."""
    if blank(v):
        return None
    if isinstance(v, (int, float)) and 1 <= int(v) <= 12:
        return int(v)
    return MONTH_LOOKUP.get(str(v).strip().lower().rstrip("."))


def clean_day(v):
    if blank(v):
        return None
    try:
        d = int(float(v))
    except (TypeError, ValueError):
        return None
    return d if 1 <= d <= 31 else None


def valid_day_month(day, month):
    # 2024 is a leap year, so 29 Feb is accepted.
    return day is not None and month is not None and day <= calendar.monthrange(2024, month)[1]


def parse_entry_date(v):
    """Returns (date | None, note | None)."""
    if blank(v):
        return None, None
    if isinstance(v, (datetime, pd.Timestamp)):
        y, m, d = v.year, v.month, v.day
        if SWAP_EXCEL_DATE_DAY_MONTH:
            if d > 12:
                return v.date(), None
            m, d = d, m
        return date(y, m, d), None
    s = str(v).strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date(), None
        except ValueError:
            pass
    return None, f"unreadable date '{s}'"


def next_occurrence(day, month, today):
    """Next date on/after today falling on day/month (29 Feb becomes 28 Feb in non-leap years)."""
    for year in (today.year, today.year + 1, today.year + 2, today.year + 4):
        d = min(day, calendar.monthrange(year, month)[1])
        candidate = date(year, month, d)
        if candidate >= today:
            return candidate
    raise ValueError("unreachable")


def fmt_day_month(day, month):
    return f"{day} {MONTHS[month - 1][:3]}"


def load_customers(path, issues):
    df = pd.read_excel(path)
    customers = []
    for i, r in enumerate(df.itertuples(index=False)):
        row = i + 2  # Excel row (header is row 1)
        first, middle, last = clean_text(r.First_Name), clean_text(r.Middle_Name), clean_text(r.Last_Name)
        name = " ".join(x for x in (first, middle, last) if x)
        if not name:
            issues.append({"row": row, "issue": "No name"})
            continue

        m1, m2 = clean_mobile(r.Mobile_1), clean_mobile(r.Mobile_2)
        for label, m in (("Mobile 1", m1), ("Mobile 2", m2)):
            if m and not mobile_is_valid(m):
                issues.append({"row": row, "name": name, "issue": f"{label} '{m}' is not a 10-digit mobile number"})

        b_day, b_month = clean_day(r.Birth_Day), clean_month(r.Birth_Month)
        a_day, a_month = clean_day(r.Anniversary_Day), clean_month(r.Anniversary_Month)
        for label, raw_d, raw_m, d, m in (
            ("Birthday", r.Birth_Day, r.Birth_Month, b_day, b_month),
            ("Anniversary", r.Anniversary_Day, r.Anniversary_Month, a_day, a_month),
        ):
            if blank(raw_d) != blank(raw_m):
                issues.append({"row": row, "name": name, "issue": f"{label} has only a day or only a month"})
            elif d and m and not valid_day_month(d, m):
                issues.append({"row": row, "name": name, "issue": f"{label} {d} {MONTHS[m - 1]} is not a real date"})
            elif (not blank(raw_d) and d is None) or (not blank(raw_m) and m is None):
                issues.append({"row": row, "name": name, "issue": f"{label} value could not be read ({raw_d} / {raw_m})"})
        # A birthday/anniversary only counts when both parts are present and form a real date.
        birthday = (b_day, b_month) if valid_day_month(b_day, b_month) else None
        anniversary = (a_day, a_month) if valid_day_month(a_day, a_month) else None

        entered, note = parse_entry_date(r[1])  # "Date of Entry"
        if note:
            issues.append({"row": row, "name": name, "issue": note})

        customers.append(
            {
                "row": row,
                "name": name,
                "mobile": m1,
                "mobile_2": m2,
                "birthday": birthday,
                "anniversary": anniversary,
                "entered": entered,
                "notes": clean_text(r.Notes),
                "_raw": {
                    "First_Name": first,
                    "Last_Name": last,
                    "Mobile_1": m1,
                    "Mobile_2": m2,
                    "Birth_Day": b_day,
                    "Birth_Month": b_month,
                    "Anniversary_Day": a_day,
                    "Anniversary_Month": a_month,
                    "Date of Entry": entered,
                },
            }
        )

    by_mobile = {}
    for c in customers:
        for m in (c["mobile"], c["mobile_2"]):
            if m:
                by_mobile.setdefault(m, []).append(c)
    for m, owners in by_mobile.items():
        if len({o["row"] for o in owners}) > 1:
            names = ", ".join(f"{o['name']} (row {o['row']})" for o in owners)
            issues.append({"issue": f"Mobile {m} is shared by: {names}"})
    return customers


def month_entries(customers, key, month, today):
    out = []
    for c in customers:
        if c[key] and c[key][1] == month:
            day = c[key][0]
            out.append(
                {
                    "row": c["row"],
                    "name": c["name"],
                    "mobile": c["mobile"],
                    "day": day,
                    "date": fmt_day_month(day, month),
                    "upcoming": month != today.month or day >= today.day,
                }
            )
    return sorted(out, key=lambda e: (e["day"], e["name"]))


def month_block(customers, key, today):
    this_m = today.month
    next_m = this_m % 12 + 1
    return {
        "current_month": {"month": MONTHS[this_m - 1], "customers": month_entries(customers, key, this_m, today)},
        "next_month": {"month": MONTHS[next_m - 1], "customers": month_entries(customers, key, next_m, today)},
    }


def upcoming(customers, today, days=30):
    end = today + timedelta(days=days)
    out = []
    for kind, key in (("Birthday", "birthday"), ("Anniversary", "anniversary")):
        for c in customers:
            if not c[key]:
                continue
            d = next_occurrence(*c[key], today)
            if d <= end:
                out.append(
                    {
                        "type": kind,
                        "row": c["row"],
                        "name": c["name"],
                        "mobile": c["mobile"],
                        "date": d.isoformat(),
                        "days_until": (d - today).days,
                    }
                )
    return sorted(out, key=lambda e: (e["date"], e["type"], e["name"]))


def signups_by_month(customers):
    counts = Counter(c["entered"].strftime("%Y-%m") for c in customers if c["entered"])
    if not counts:
        return []
    first, last = min(counts), max(counts)
    y, m = map(int, first.split("-"))
    series = []
    while True:
        key = f"{y:04d}-{m:02d}"
        series.append({"month": key, "label": f"{MONTHS[m - 1][:3]} {y}", "count": counts.get(key, 0)})
        if key == last:
            return series
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def completeness(customers):
    total = len(customers)
    out = []
    for key, label in FIELDS:
        present = sum(1 for c in customers if c["_raw"][key] is not None)
        entry = {
            "field": key,
            "label": label,
            "present": present,
            "missing": total - present,
            "pct_complete": round(100 * present / total, 1) if total else 0,
        }
        if key in ("Mobile_1", "Mobile_2"):
            entry["invalid"] = sum(1 for c in customers if c["_raw"][key] and not mobile_is_valid(c["_raw"][key]))
        out.append(entry)
    return out


def build(path, today):
    issues = []
    customers = load_customers(path, issues)
    total = len(customers)

    def pct(n):
        return round(100 * n / total, 1) if total else 0

    no_mobile = sum(1 for c in customers if not c["mobile"] and not c["mobile_2"])
    no_birthday = sum(1 for c in customers if not c["birthday"])
    no_anniversary = sum(1 for c in customers if not c["anniversary"])
    birthdays = month_block(customers, "birthday", today)
    anniversaries = month_block(customers, "anniversary", today)

    dist_b = [sum(1 for c in customers if c["birthday"] and c["birthday"][1] == m) for m in range(1, 13)]
    dist_a = [sum(1 for c in customers if c["anniversary"] and c["anniversary"][1] == m) for m in range(1, 13)]
    signups = signups_by_month(customers)

    data = {
        "meta": {
            "as_of": today.isoformat(),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_file": Path(path).name,
        },
        "kpis": {
            "total_customers": total,
            "missing_mobile": no_mobile,
            "missing_mobile_pct": pct(no_mobile),
            "missing_birthday": no_birthday,
            "missing_birthday_pct": pct(no_birthday),
            "missing_anniversary": no_anniversary,
            "missing_anniversary_pct": pct(no_anniversary),
            "birthdays_this_month": len(birthdays["current_month"]["customers"]),
            "birthdays_upcoming_this_month": sum(e["upcoming"] for e in birthdays["current_month"]["customers"]),
            "birthdays_next_month": len(birthdays["next_month"]["customers"]),
            "anniversaries_this_month": len(anniversaries["current_month"]["customers"]),
            "anniversaries_next_month": len(anniversaries["next_month"]["customers"]),
        },
        "completeness": completeness(customers),
        "birthdays": birthdays,
        "anniversaries": anniversaries,
        "distribution_by_month": {"months": [m[:3] for m in MONTHS], "birthdays": dist_b, "anniversaries": dist_a},
        "signups_by_month": signups,
        "signups_meta": {
            "with_date": sum(1 for c in customers if c["entered"]),
            "without_date": sum(1 for c in customers if not c["entered"]),
        },
        "upcoming_30_days": upcoming(customers, today, 30),
        "customers": [
            {
                "row": c["row"],
                "name": c["name"],
                "mobile": c["mobile"],
                "mobile_2": c["mobile_2"],
                "birth_day": c["birthday"][0] if c["birthday"] else None,
                "birth_month": c["birthday"][1] if c["birthday"] else None,
                "anniversary_day": c["anniversary"][0] if c["anniversary"] else None,
                "anniversary_month": c["anniversary"][1] if c["anniversary"] else None,
                "entered": c["entered"].isoformat() if c["entered"] else None,
                "notes": c["notes"],
            }
            for c in customers
        ],
        "data_quality": issues,
    }
    return data


def write_js_copy(json_text):
    """Same data as a script file: browsers block fetch() of a JSON file when a page is opened from disk,
    but a <script src> still loads."""
    OUTPUT_JS.write_text(f"window.DASHBOARD_DATA = {json_text};\n", encoding="utf-8")


def find_excel():
    matches = sorted(HERE.glob("Salon Customers Database*.xlsx"))
    if not matches:
        sys.exit("No 'Salon Customers Database*.xlsx' found next to this script. Use --input <file>.")
    return matches[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, help="Excel file (default: the Salon Customers Database file here)")
    ap.add_argument("--today", type=date.fromisoformat, default=date.today(), help="YYYY-MM-DD, defaults to today")
    args = ap.parse_args()

    data = build(args.input or find_excel(), args.today)
    OUTPUT_JSON.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    write_js_copy(json.dumps(data, ensure_ascii=False))

    k = data["kpis"]
    print(f"Wrote {OUTPUT_JSON.name}: {k['total_customers']} customers, as of {data['meta']['as_of']}")
    print(f"  missing mobile {k['missing_mobile_pct']}% | missing birthday {k['missing_birthday_pct']}% "
          f"| birthdays this month {k['birthdays_this_month']} (next month {k['birthdays_next_month']})")
    print(f"  {len(data['upcoming_30_days'])} birthdays/anniversaries in the next 30 days; "
          f"{len(data['data_quality'])} data-quality notes")
    print(f"  also wrote {OUTPUT_JS.name} (lets dashboard.html open straight from disk)")


if __name__ == "__main__":
    main()
