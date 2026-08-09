from datetime import datetime, date
import calendar as _cal


def _normalize_name(name: str) -> str:
    import unicodedata, re
    s = unicodedata.normalize('NFD', (name or '').strip().lower())
    s = s.encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^a-z0-9]', '', s)
    return s


def _safe_txt(t, default="-"):
    import re
    if t is None:
        return default
    s = str(t)
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    return s.encode('latin-1', errors='replace').decode('latin-1')


def _calendar_event_dict(row):
    data = dict(row)
    try:
        due = datetime.strptime(
            str(data.get("due_date") or ""),
            "%Y-%m-%d",
        ).date()
        today = date.today()
        days_left = (due - today).days
        data["days_left"] = days_left
        data["in_reminder_window"] = (
            data.get("status") == "pending"
            and 0 <= days_left <= int(data.get("notify_days_before") or 2)
        )
    except Exception:
        data["days_left"] = None
        data["in_reminder_window"] = False
    return data


def _add_months(date_str: str, months: int) -> str:
    base = datetime.strptime(date_str, "%Y-%m-%d").date()
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    day = min(base.day, _cal.monthrange(year, month)[1])
    return date(year, month, day).isoformat()
