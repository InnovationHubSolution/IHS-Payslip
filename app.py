import csv
import json
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import Flask, render_template, request, redirect, url_for


def week_start(date_str):
    """Return Monday (YYYY-MM-DD) of the week containing date_str."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        delta = dt.weekday()  # Monday=0
        mon = dt.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=delta)
        return mon.strftime("%Y-%m-%d")
    except ValueError:
        return None


def same_week(date_str, week_ref):
    """True if date_str falls in the same week (Mon–Sun) as week_ref (any day as YYYY-MM-DD)."""
    ws1 = week_start(date_str)
    ws2 = week_start(week_ref)
    return ws1 and ws2 and ws1 == ws2

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDS_FILE = os.path.join(BASE_DIR, "worker_records.csv")
RECORDS_FILE_JSON = os.path.join(BASE_DIR, "worker_records.json")  # legacy, for migration
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

CSV_COLUMNS = ["date", "date_display", "worker_name", "in_time", "out_time", "break_minutes", "hours_worked", "hours_value", "total_pay", "paid"]


def load_settings():
    defaults = {
        "hourly_rate": None,
        "break_minutes": None,
        # Employee VNPF % withheld from gross pay on payslips (default 6%; see VNPF employers page for official rates)
        "vnpf_employee_rate_percent": 6.0,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {**defaults, **data}
        except (json.JSONDecodeError, IOError):
            pass
    return dict(defaults)


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def load_vnpf_employee_rate_percent():
    """VNPF employee deduction % of gross remuneration shown on payslips."""
    s = load_settings()
    r = s.get("vnpf_employee_rate_percent")
    if r is None:
        return 6.0
    try:
        v = float(r)
        return max(0.0, min(100.0, v))
    except (TypeError, ValueError):
        return 6.0


def vnpf_deduction_from_gross(gross, rate_percent):
    """Employee VNPF amount from gross pay (Vt)."""
    if gross is None or not isinstance(gross, (int, float)):
        return 0.0
    return round(float(gross) * (float(rate_percent) / 100.0), 2)


def load_records():
    # One-time migration: if JSON exists and CSV does not, migrate
    if os.path.exists(RECORDS_FILE_JSON) and not os.path.exists(RECORDS_FILE):
        try:
            with open(RECORDS_FILE_JSON, "r") as f:
                records = json.load(f)
            save_records(records)
        except (json.JSONDecodeError, IOError):
            pass
    if os.path.exists(RECORDS_FILE):
        try:
            with open(RECORDS_FILE, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = []
                for r in reader:
                    # Restore types
                    hv = r.get("hours_value", "")
                    r["hours_value"] = float(hv) if hv and hv.strip() else 0.0
                    tp = r.get("total_pay", "")
                    r["total_pay"] = float(tp) if tp and tp.strip() else None
                    bm = r.get("break_minutes", "")
                    r["break_minutes"] = int(bm) if bm and str(bm).strip().isdigit() else 0
                    r["paid"] = (r.get("paid", "").strip().lower() in ("1", "true", "yes"))
                    rows.append(r)
                return rows
        except (IOError, ValueError):
            pass
    return []


def save_records(records):
    with open(RECORDS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            row = {}
            for k in CSV_COLUMNS:
                v = r.get(k)
                if v is None and k in ("total_pay", "hours_value"):
                    row[k] = "" if k == "total_pay" else "0"
                elif k == "paid":
                    row[k] = "1" if r.get("paid") else "0"
                elif k == "break_minutes":
                    row[k] = "" if r.get("break_minutes") is None else str(int(r.get("break_minutes") or 0))
                else:
                    row[k] = "" if v is None else v
            writer.writerow(row)


def parse_time(s: str):
    """Parse time string (HH:MM or H:MM AM/PM) to minutes since midnight."""
    if not s or not s.strip():
        return None
    s = s.strip()
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%H:%M:%S"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            continue
    return None


def minutes_to_hours_str(minutes: float) -> str:
    """Convert minutes to 'Xh Ym' or decimal hours."""
    if minutes is None:
        return ""
    h = int(minutes // 60)
    m = int(round(minutes % 60))
    if m == 0:
        return f"{h}"
    return f"{h}.{m * 100 // 60:.0f}" if m else f"{h}"


def date_to_display(date_str: str) -> str:
    """Convert YYYY-MM-DD to M/D/YY like 7/3/26."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        return f"{dt.month}/{dt.day}/{dt.strftime('%y')}"
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
            return f"{dt.month}/{dt.day}/{dt.strftime('%y')}"
        except ValueError:
            return date_str


def date_to_storage(display_date: str) -> str:
    """Convert M/D/YY or M/D/YYYY to YYYY-MM-DD for storage."""
    if not display_date or not display_date.strip():
        return ""
    s = display_date.strip()
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s


def compute_record(date_str, worker_name, time_in, time_out, hourly_rate_str, break_minutes=0):
    """Compute hours worked and total pay for one record. Break time is subtracted from total."""
    min_in = parse_time(time_in) if time_in else None
    min_out = parse_time(time_out) if time_out else None
    total_minutes = None
    if min_in is not None and min_out is not None:
        if min_out <= min_in:
            total_minutes = (24 * 60 - min_in) + min_out
        else:
            total_minutes = min_out - min_in
        if total_minutes is not None and break_minutes:
            total_minutes = max(0, total_minutes - int(break_minutes))

    hours = total_minutes / 60.0 if total_minutes is not None else 0
    hourly_rate = None
    if hourly_rate_str:
        try:
            hourly_rate = float(hourly_rate_str)
            if hourly_rate < 0:
                hourly_rate = None
        except ValueError:
            pass
    total_pay = round(hours * hourly_rate, 2) if hourly_rate is not None else None

    return {
        "date": date_to_storage(date_str) or date_str,
        "date_display": date_to_display(date_to_storage(date_str) or date_str) or date_str,
        "worker_name": (worker_name or "").strip(),
        "in_time": (time_in or "").strip(),
        "out_time": (time_out or "").strip(),
        "break_minutes": int(break_minutes) if break_minutes else 0,
        "hours_worked": minutes_to_hours_str(total_minutes) if total_minutes is not None else "",
        "hours_value": hours,
        "total_pay": total_pay,
        "paid": False,
    }


def record_hours(record):
    """Get hours worked for a record from in_time/out_time minus break_minutes, or hours_value."""
    min_in = parse_time(record.get("in_time") or "")
    min_out = parse_time(record.get("out_time") or "")
    break_min = int(record.get("break_minutes") or 0)
    if min_in is not None and min_out is not None:
        if min_out <= min_in:
            total_minutes = (24 * 60 - min_in) + min_out
        else:
            total_minutes = min_out - min_in
        total_minutes = max(0, total_minutes - break_min)
        return total_minutes / 60.0
    return record.get("hours_value", 0.0)


def update_all_records_with_rate(hourly_rate):
    """Recalculate total_pay for every record using the given hourly rate. Saves to disk."""
    records = load_records()
    for r in records:
        hours = record_hours(r)
        r["total_pay"] = round(hours * hourly_rate, 2) if hourly_rate is not None else None
    save_records(records)


@app.route("/", methods=["GET", "POST"])
def index():
    records = load_records()
    errors = []
    filter_worker = (request.args.get("worker") or "").strip()
    filter_week = (request.args.get("week") or "").strip()
    filter_from = (request.args.get("from") or "").strip()
    filter_to = (request.args.get("to") or "").strip()
    hide_paid = "1" in request.args.getlist("hide_paid") or request.args.get("hide_paid", "1") == "1"

    def redirect_index():
        q = {
            "worker": filter_worker or None,
            "week": filter_week or None,
            "from": filter_from or None,
            "to": filter_to or None,
            "hide_paid": "1" if hide_paid else "0",
        }
        q = {k: v for k, v in q.items() if v is not None}
        return redirect(url_for("index") + ("?" + urlencode(q) if q else ""))

    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "delete":
            try:
                idx = int(request.form.get("index", -1))
                if 0 <= idx < len(records):
                    records.pop(idx)
                    save_records(records)
            except ValueError:
                pass
            return redirect_index()

        if action == "mark_paid":
            try:
                idx = int(request.form.get("index", -1))
                if 0 <= idx < len(records):
                    records[idx]["paid"] = True
                    save_records(records)
            except ValueError:
                pass
            return redirect_index()

        if action == "mark_all_paid":
            for key in request.form:
                if key.startswith("index_"):
                    try:
                        idx = int(request.form.get(key))
                        if 0 <= idx < len(records):
                            records[idx]["paid"] = True
                    except (ValueError, TypeError):
                        pass
            save_records(records)
            return redirect_index()

        if action == "mark_week_paid":
            pay_week = (request.form.get("pay_week") or "").strip()
            pay_worker = (request.form.get("pay_worker") or "").strip()
            if pay_week:
                for r in records:
                    if same_week(r.get("date") or "", pay_week):
                        if not pay_worker or pay_worker.lower() in (r.get("worker_name") or "").lower():
                            r["paid"] = True
                save_records(records)
            return redirect_index()

        if action == "mark_range_paid":
            pay_from = (request.form.get("pay_from") or "").strip()
            pay_to = (request.form.get("pay_to") or "").strip()
            pay_worker = (request.form.get("pay_worker") or "").strip()
            if pay_from or pay_to:
                for r in records:
                    rd = r.get("date") or ""
                    if pay_from and rd < pay_from:
                        continue
                    if pay_to and rd > pay_to:
                        continue
                    if pay_worker and pay_worker.lower() not in (r.get("worker_name") or "").lower():
                        continue
                    r["paid"] = True
                save_records(records)
            return redirect_index()

        # Add new record
        date_str = (request.form.get("date") or "").strip()
        worker_name = (request.form.get("worker_name") or "").strip()
        time_in = (request.form.get("time_in") or "").strip()
        time_out = (request.form.get("time_out") or "").strip()
        break_minutes = (request.form.get("break_minutes") or "").strip()
        hourly_rate_str = (request.form.get("hourly_rate") or "").strip()
        settings = load_settings()
        if not hourly_rate_str and settings.get("hourly_rate") is not None:
            hourly_rate_str = str(settings["hourly_rate"])
        if not break_minutes and settings.get("break_minutes") is not None:
            break_minutes = str(settings["break_minutes"])

        if not worker_name:
            errors.append("Worker name is required.")
        if not date_str:
            errors.append("Date is required.")
        if not time_in:
            errors.append("In time is required.")
        if not time_out:
            errors.append("Out time is required.")

        if not errors:
            rec = compute_record(date_str, worker_name, time_in, time_out, hourly_rate_str, break_minutes)
            records.append(rec)
            records.sort(key=lambda r: (r.get("date") or "", r.get("worker_name") or ""))
            save_records(records)
            return redirect_index()

    # Ensure stored records have date_display, paid, break_minutes
    for r in records:
        if r.get("paid") is None:
            r["paid"] = False
        if r.get("break_minutes") is None:
            r["break_minutes"] = 0
        if "date_display" not in r and r.get("date"):
            r["date_display"] = date_to_display(r["date"])
        if "hours_worked" not in r and r.get("in_time") and r.get("out_time"):
            comp = compute_record(
                r.get("date", ""),
                r.get("worker_name", ""),
                r.get("in_time", ""),
                r.get("out_time", ""),
                r.get("hourly_rate", "") or "",
                r.get("break_minutes", 0),
            )
            r["hours_worked"] = comp["hours_worked"]
            r["total_pay"] = comp["total_pay"]

    # Sort by date (then worker name for same day)
    records.sort(key=lambda r: (r.get("date") or "", r.get("worker_name") or ""))

    # Filter by worker, week, and/or date range; optionally hide paid
    def match(r, i):
        if filter_worker and filter_worker.lower() not in (r.get("worker_name") or "").lower():
            return False
        if filter_week and not same_week(r.get("date") or "", filter_week):
            return False
        rd = r.get("date") or ""
        if filter_from and rd < filter_from:
            return False
        if filter_to and rd > filter_to:
            return False
        if hide_paid and r.get("paid"):
            return False
        return True

    filtered = [(i, records[i]) for i in range(len(records)) if match(records[i], i)]
    display_records = []
    record_indices = []
    for i, r in filtered:
        r = dict(r)
        r["_index"] = i
        display_records.append(r)
        record_indices.append(i)

    # Payout totals: only unpaid (don't count already paid)
    def unpaid_pay(r):
        return (r.get("total_pay") or 0) if not r.get("paid") and isinstance(r.get("total_pay"), (int, float)) else 0
    total_earnings = sum(unpaid_pay(r) for r in display_records)
    total_all = sum(unpaid_pay(r) for r in records)
    settings = load_settings()
    return render_template(
        "index.html",
        records=display_records,
        errors=errors,
        default_hourly_rate=settings.get("hourly_rate"),
        default_break_minutes=settings.get("break_minutes"),
        total_earnings=total_earnings,
        total_all=total_all,
        filter_worker=filter_worker,
        filter_week=filter_week,
        filter_from=filter_from,
        filter_to=filter_to,
        hide_paid=hide_paid,
        record_indices=record_indices,
    )


@app.route("/record/<int:index>/edit", methods=["GET", "POST"])
def edit_record(index):
    records = load_records()
    records.sort(key=lambda r: (r.get("date") or "", r.get("worker_name") or ""))
    if index < 0 or index >= len(records):
        return redirect(url_for("index"))
    record = records[index]
    errors = []
    if request.method == "POST":
        date_str = (request.form.get("date") or "").strip()
        worker_name = (request.form.get("worker_name") or "").strip()
        time_in = (request.form.get("time_in") or "").strip()
        time_out = (request.form.get("time_out") or "").strip()
        break_minutes = (request.form.get("break_minutes") or "").strip()
        if not worker_name:
            errors.append("Worker name is required.")
        if not date_str:
            errors.append("Date is required.")
        if not time_in:
            errors.append("In time is required.")
        if not time_out:
            errors.append("Out time is required.")
        if not errors:
            settings = load_settings()
            hourly_rate_str = str(settings["hourly_rate"]) if settings.get("hourly_rate") is not None else ""
            if not break_minutes and settings.get("break_minutes") is not None:
                break_minutes = str(settings["break_minutes"])
            rec = compute_record(date_str, worker_name, time_in, time_out, hourly_rate_str, break_minutes)
            rec["paid"] = record.get("paid", False)
            records[index] = rec
            save_records(records)
            return redirect(url_for("index"))
    return render_template(
        "edit_record.html",
        record=record,
        index=index,
        errors=errors,
    )


def _payout_redirect(worker="", week="", from_="", to=""):
    q = {k: v for k, v in [("worker", worker), ("week", week), ("from", from_), ("to", to)] if v}
    return redirect(url_for("payout") + ("?" + urlencode(q) if q else ""))


def _filtered_url(endpoint, worker="", week="", from_="", to=""):
    q = {k: v for k, v in [("worker", worker), ("week", week), ("from", from_), ("to", to)] if v}
    return url_for(endpoint) + ("?" + urlencode(q) if q else "")


def record_matches_filters(record, worker="", week="", from_="", to="", unpaid_only=False):
    if unpaid_only and record.get("paid"):
        return False
    if worker and worker.lower() not in (record.get("worker_name") or "").lower():
        return False
    if week and not same_week(record.get("date") or "", week):
        return False
    rec_date = record.get("date") or ""
    if from_ and rec_date < from_:
        return False
    if to and rec_date > to:
        return False
    return True


@app.route("/payout", methods=["GET", "POST"])
def payout():
    records = load_records()
    filter_worker = (request.args.get("worker") or "").strip()
    filter_week = (request.args.get("week") or "").strip()
    filter_from = (request.args.get("from") or "").strip()
    filter_to = (request.args.get("to") or "").strip()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "mark_week_paid":
            pay_week = (request.form.get("pay_week") or "").strip()
            pay_worker = (request.form.get("pay_worker") or "").strip()
            if pay_week:
                for r in records:
                    if same_week(r.get("date") or "", pay_week):
                        if not pay_worker or pay_worker.lower() in (r.get("worker_name") or "").lower():
                            r["paid"] = True
                save_records(records)
            return _payout_redirect(filter_worker, filter_week, filter_from, filter_to)

        if action == "mark_range_paid":
            pay_from = (request.form.get("pay_from") or "").strip()
            pay_to = (request.form.get("pay_to") or "").strip()
            pay_worker = (request.form.get("pay_worker") or "").strip()
            if pay_from or pay_to:
                for r in records:
                    rd = r.get("date") or ""
                    if pay_from and rd < pay_from:
                        continue
                    if pay_to and rd > pay_to:
                        continue
                    if pay_worker and pay_worker.lower() not in (r.get("worker_name") or "").lower():
                        continue
                    r["paid"] = True
                save_records(records)
            return _payout_redirect(filter_worker, filter_week, filter_from, filter_to)

    # Ensure records have date_display, paid
    for r in records:
        if r.get("paid") is None:
            r["paid"] = False
        if "date_display" not in r and r.get("date"):
            r["date_display"] = date_to_display(r["date"])

    # Sort by date (then worker name for same day)
    records.sort(key=lambda r: (r.get("date") or "", r.get("worker_name") or ""))

    unpaid_records = []
    for i, r in enumerate(records):
        if record_matches_filters(r, filter_worker, filter_week, filter_from, filter_to, unpaid_only=True):
            rec = dict(r)
            rec["_index"] = i
            unpaid_records.append(rec)

    def unpaid_pay(r):
        return (r.get("total_pay") or 0) if isinstance(r.get("total_pay"), (int, float)) else 0
    total_unpaid = sum(unpaid_pay(r) for r in unpaid_records)
    total_unpaid_all = sum(unpaid_pay(r) for r in records if not r.get("paid"))

    return render_template(
        "payout.html",
        records=unpaid_records,
        total_unpaid=total_unpaid,
        total_unpaid_all=total_unpaid_all,
        filter_worker=filter_worker,
        filter_week=filter_week,
        filter_from=filter_from,
        filter_to=filter_to,
        payslip_url=_filtered_url("payslip", filter_worker, filter_week, filter_from, filter_to),
    )


@app.route("/payslip", methods=["GET", "POST"])
def payslip():
    records = load_records()
    filter_worker = (request.args.get("worker") or "").strip()
    filter_week = (request.args.get("week") or "").strip()
    filter_from = (request.args.get("from") or "").strip()
    filter_to = (request.args.get("to") or "").strip()

    # Ensure records have date_display, paid, break_minutes
    for r in records:
        if r.get("paid") is None:
            r["paid"] = False
        if r.get("break_minutes") is None:
            r["break_minutes"] = 0
        if "date_display" not in r and r.get("date"):
            r["date_display"] = date_to_display(r["date"])

    if request.method == "POST":
        if request.form.get("action") == "mark_selection_paid":
            for r in records:
                if record_matches_filters(r, filter_worker, filter_week, filter_from, filter_to, unpaid_only=True):
                    r["paid"] = True
            save_records(records)
        return _payout_redirect(filter_worker, filter_week, filter_from, filter_to)

    records.sort(key=lambda r: (r.get("date") or "", r.get("worker_name") or ""))
    payslip_records = [
        dict(r) for r in records
        if record_matches_filters(r, filter_worker, filter_week, filter_from, filter_to, unpaid_only=True)
    ]
    vnpf_rate = load_vnpf_employee_rate_percent()
    payslip_rows = []
    for r in payslip_records:
        row = dict(r)
        gross = row.get("total_pay")
        vnpf_amt = vnpf_deduction_from_gross(gross, vnpf_rate)
        row["vnpf_amount"] = vnpf_amt
        if gross is not None and isinstance(gross, (int, float)):
            row["net_after_vnpf"] = round(float(gross) - vnpf_amt, 2)
        else:
            row["net_after_vnpf"] = None
        payslip_rows.append(row)

    def gross_pay(rec):
        return (rec.get("total_pay") or 0) if isinstance(rec.get("total_pay"), (int, float)) else 0

    total_payout = sum(gross_pay(r) for r in payslip_rows)
    total_vnpf = sum((r.get("vnpf_amount") or 0) for r in payslip_rows)
    total_net_after_vnpf = sum(
        (r.get("net_after_vnpf") or 0) for r in payslip_rows if r.get("net_after_vnpf") is not None
    )
    workers = sorted({(r.get("worker_name") or "").strip() for r in payslip_rows if (r.get("worker_name") or "").strip()})
    worker_label = workers[0] if len(workers) == 1 else ("Multiple workers" if workers else "No worker selected")
    period_label = "All unpaid records"
    if filter_week:
        period_label = f"Week of {date_to_display(filter_week)}"
    elif filter_from or filter_to:
        period_label = f"{date_to_display(filter_from) if filter_from else 'Beginning'} to {date_to_display(filter_to) if filter_to else 'Now'}"

    return render_template(
        "payslip.html",
        records=payslip_rows,
        total_payout=total_payout,
        total_vnpf=total_vnpf,
        total_net_after_vnpf=total_net_after_vnpf,
        vnpf_rate_percent=vnpf_rate,
        worker_label=worker_label,
        workers=workers,
        period_label=period_label,
        generated_on=datetime.now().strftime("%m/%d/%Y %I:%M %p"),
        filter_worker=filter_worker,
        filter_week=filter_week,
        filter_from=filter_from,
        filter_to=filter_to,
        payout_url=_filtered_url("payout", filter_worker, filter_week, filter_from, filter_to),
        payslip_self_url=_filtered_url("payslip", filter_worker, filter_week, filter_from, filter_to),
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    settings_data = load_settings()
    message = None
    if request.method == "POST":
        hourly_rate_str = (request.form.get("hourly_rate") or "").strip()
        break_minutes_str = (request.form.get("break_minutes") or "").strip()
        vnpf_rate_str = (request.form.get("vnpf_employee_rate_percent") or "").strip()
        # Break minutes
        if break_minutes_str:
            try:
                bm = int(break_minutes_str)
                if bm >= 0:
                    settings_data["break_minutes"] = bm
                else:
                    message = "Break minutes must be 0 or greater."
            except ValueError:
                message = "Break minutes must be a whole number."
        else:
            settings_data["break_minutes"] = None
        # VNPF employee % (payslip deduction from gross)
        if message is None:
            if vnpf_rate_str:
                try:
                    vr = float(vnpf_rate_str)
                    if 0 <= vr <= 100:
                        settings_data["vnpf_employee_rate_percent"] = vr
                    else:
                        message = "VNPF employee rate must be between 0 and 100."
                except ValueError:
                    message = "Please enter a valid number for VNPF employee %."
            else:
                settings_data["vnpf_employee_rate_percent"] = 6.0
        # Hourly rate
        if message is None:
            if hourly_rate_str:
                try:
                    rate = float(hourly_rate_str)
                    if rate >= 0:
                        settings_data["hourly_rate"] = rate
                        save_settings(settings_data)
                        update_all_records_with_rate(rate)
                        message = "Settings saved. All records updated to the new rate."
                    else:
                        message = "Hourly rate must be 0 or greater."
                except ValueError:
                    message = "Please enter a valid number for hourly rate."
            else:
                settings_data["hourly_rate"] = None
                save_settings(settings_data)
                update_all_records_with_rate(None)
                message = "Default hourly rate cleared. Total pay removed from all records."
        if message is None:
            save_settings(settings_data)
            message = "Settings saved."
    def _vnpf_display_from_settings(sd):
        try:
            v = float(sd.get("vnpf_employee_rate_percent", 6.0))
            return max(0.0, min(100.0, v))
        except (TypeError, ValueError):
            return 6.0

    return render_template(
        "settings.html",
        hourly_rate=settings_data.get("hourly_rate"),
        break_minutes=settings_data.get("break_minutes"),
        vnpf_employee_rate_percent=_vnpf_display_from_settings(settings_data),
        message=message,
    )


if __name__ == "__main__":
    port = 5000
    print(f"\n  Worker Records app: http://127.0.0.1:{port}/\n  Open this URL in Chrome, Safari, or Firefox (not Cursor's built-in browser).\n")
    app.run(debug=True, host="127.0.0.1", port=port)
