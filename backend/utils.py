from datetime import datetime, date
import calendar as _cal
import json


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


def _wa_failure_hint(detail: str) -> str:
    low=(detail or "").lower()
    if "401" in low or "403" in low or "unauthorized" in low or "forbidden" in low: return "Token/API Key recusado. Confira a credencial no provedor."
    if "404" in low or "not found" in low: return "Endpoint ou instancia nao encontrado. Confira URL e Instance ID."
    if "429" in low or "limit" in low: return "Limite de envios atingido. Aguarde ou confira o plano do provedor."
    if "timeout" in low or "timed out" in low: return "A API nao respondeu no prazo. Verifique se o servico esta online."
    if "connection" in low or "refused" in low or "connect" in low: return "Confira URL, porta, firewall e se o servico do WhatsApp esta ativo."
    if "configurada" in low or "configurado" in low: return "Preencha URL da API e token e salve a configuracao."
    return "Confira token, instancia, conexao do WhatsApp e formato do telefone."


def _wa_log_response(result: dict, cfg: dict) -> str:
    detail=str(result.get("response") or "Sem resposta do provedor.")
    return json.dumps({"provider":cfg.get("provider","ultramsg"),"response":detail,
                       "hint":_wa_failure_hint(detail) if not result.get("ok") else ""},ensure_ascii=False)[:2000]
