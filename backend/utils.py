from datetime import datetime, date
import calendar as _cal


def _add_months(date_str: str, months: int) -> str:
    base = datetime.strptime(date_str, "%Y-%m-%d").date()
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    day = min(base.day, _cal.monthrange(year, month)[1])
    return date(year, month, day).isoformat()
