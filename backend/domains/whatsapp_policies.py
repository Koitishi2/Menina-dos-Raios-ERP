import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional


OPT_OUT_WORDS = frozenset({"SAIR", "PARAR", "CANCELAR", "STOP"})
HUMAN_WORDS = frozenset({"ATENDENTE", "HUMANO", "FALAR COM ATENDENTE"})


@dataclass(frozen=True)
class NormalizedPhone:
    raw: str
    digits: str
    e164: str
    jid: str
    valid: bool
    reason: str = ""


def normalize_brazil_phone(value: str) -> NormalizedPhone:
    raw = str(value or "").strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) in (10, 11):
        digits = "55" + digits
    if not digits:
        return NormalizedPhone(raw, "", "", "", False, "telefone_ausente")
    if not digits.startswith("55"):
        return NormalizedPhone(raw, digits, "", "", False, "pais_nao_suportado")
    if len(digits) not in (12, 13):
        return NormalizedPhone(raw, digits, "", "", False, "quantidade_digitos_invalida")
    area_code = digits[2:4]
    subscriber = digits[4:]
    if area_code.startswith("0") or subscriber.startswith(("0", "1")):
        return NormalizedPhone(raw, digits, "", "", False, "numero_invalido")
    return NormalizedPhone(raw, digits, f"+{digits}", f"{digits}@s.whatsapp.net", True)


def normalize_command(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().upper()


def conversation_control_intent(value: str) -> Optional[str]:
    command = normalize_command(value)
    if command in OPT_OUT_WORDS:
        return "opt_out"
    if command in HUMAN_WORDS or re.search(r"\b(ATENDENTE|HUMANO)\b", command) or command == "3":
        return "atendimento_humano"
    if command == "4":
        return "opt_out"
    return None


def message_idempotency_key(
    company_key: str,
    external_message_id: str,
    jid: str,
    received_at: str,
    payload: object,
) -> str:
    canonical = json.dumps(
        {
            "company": str(company_key or "").strip().lower(),
            "external_message_id": str(external_message_id or "").strip(),
            "jid": str(jid or "").strip().lower(),
            "received_at": str(received_at or "").strip(),
            "payload": payload,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def campaign_eligibility(
    days_without_purchase: int,
    consent_state: str,
    has_open_conversation: bool = False,
    has_pending_order: bool = False,
) -> tuple[bool, str]:
    if consent_state != "opt_in":
        return False, "sem_consentimento"
    if has_open_conversation:
        return False, "conversa_aberta"
    if has_pending_order:
        return False, "pedido_pendente"
    if int(days_without_purchase) <= 7:
        return False, "intervalo_insuficiente"
    return True, "mais_de_7_dias_sem_compra"


def duplicate_order_reasons(
    message_processed: bool,
    open_order_for_conversation: bool,
    idempotency_key_exists: bool,
    already_confirmed: bool,
    recent_client_order_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    reasons = []
    if message_processed:
        reasons.append("mensagem_processada")
    if open_order_for_conversation:
        reasons.append("pedido_aberto_na_conversa")
    if idempotency_key_exists:
        reasons.append("idempotency_key_repetida")
    if already_confirmed:
        reasons.append("pedido_ja_confirmado")
    if tuple(recent_client_order_ids):
        reasons.append("pedido_recente_do_cliente")
    return tuple(reasons)


def order_contract_issues(
    company_key: str,
    client_id: str,
    conversation_id: str,
    source_company_key: str,
) -> tuple[str, ...]:
    issues = []
    if not str(client_id or "").strip():
        issues.append("cliente_ausente")
    if not str(conversation_id or "").strip():
        issues.append("conversa_ausente")
    if str(company_key or "").strip().lower() != str(source_company_key or "").strip().lower():
        issues.append("empresa_divergente")
    return tuple(issues)


def user_can(permission: str, granted_permissions: Iterable[str]) -> bool:
    return str(permission or "").strip() in frozenset(granted_permissions or ())


def baileys_readiness(
    connected: bool,
    credentials_available: bool,
    connection_error: Optional[str] = None,
) -> tuple[bool, str]:
    if connection_error:
        return False, "erro_conexao"
    if not credentials_available:
        return False, "credenciais_ausentes"
    if not connected:
        return False, "baileys_desconectado"
    return True, "disponivel"
