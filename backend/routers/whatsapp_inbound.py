import hmac
import json
import logging
import os
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

try:
    from ..repositories import whatsapp_repository as repository
    from .whatsapp_campaigns import outbound_settings
    from ..services.whatsapp_inbound_service import process_inbound_event
except ImportError:
    from repositories import whatsapp_repository as repository
    from routers.whatsapp_campaigns import outbound_settings
    from services.whatsapp_inbound_service import process_inbound_event


logger = logging.getLogger("menina.whatsapp.inbound")
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


class BaileysInboundEvent(BaseModel):
    provider: str = Field(pattern="^baileys$")
    instance: str = Field(min_length=1, max_length=100)
    event_id: str = Field(min_length=1, max_length=255)
    message_id: str = Field(min_length=1, max_length=255)
    remote_jid: str = Field(min_length=1, max_length=255)
    remote_jid_alt: str | None = Field(default=None, max_length=255)
    participant_alt: str | None = Field(default=None, max_length=255)
    from_me: bool = False
    message_type: str = Field(min_length=1, max_length=100)
    text: str = Field(default="", max_length=10000)
    timestamp: str = Field(min_length=1, max_length=64)
    raw_type: str | None = Field(default=None, max_length=100)


def inbound_settings():
    return {
        "enabled": os.environ.get("WHATSAPP_INBOUND_ENABLED", "false").strip().lower() in TRUE_VALUES,
        "token": os.environ.get("WHATSAPP_INBOUND_TOKEN", "").strip(),
        "instance": os.environ.get("WHATSAPP_INBOUND_INSTANCE", "").strip(),
        "company": os.environ.get("WHATSAPP_INBOUND_COMPANY", "").strip().lower(),
        "max_body": max(1024, min(int(os.environ.get("WHATSAPP_INBOUND_MAX_BODY_BYTES", "32768")), 1048576)),
    }


def _require_local_request(request):
    host = request.client.host if request.client else ""
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
    if host not in LOOPBACK_HOSTS or forwarded:
        raise HTTPException(403, "Canal interno disponivel somente via loopback.")


async def _read_limited_json(request, max_bytes):
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        raise HTTPException(415, "Content-Type deve ser application/json.")
    try:
        declared = int(request.headers.get("content-length", "0") or 0)
    except ValueError:
        raise HTTPException(400, "Content-Length invalido.")
    if declared > max_bytes:
        raise HTTPException(413, "Evento excede o limite permitido.")
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(413, "Evento excede o limite permitido.")
        chunks.append(chunk)
    try:
        value = json.loads(b"".join(chunks).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(400, "JSON invalido.") from exc
    if not isinstance(value, dict):
        raise HTTPException(400, "Evento deve ser um objeto JSON.")
    return value


def _evo_value(obj, *paths):
    for path in paths:
        value = obj
        for key in path.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if value not in (None, ""):
            return value
    return None


def _normalize_evolution_go(raw):
    if raw.get("event") not in ("Message", "messages.upsert", "MESSAGE"):
        return None
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    info = data.get("Info") or data.get("info") or {}
    key = data.get("key") if isinstance(data.get("key"), dict) else {}
    message = data.get("Message") or data.get("message") or {}
    jid = _evo_value(info, "Chat", "chat", "MessageSource.Chat", "messageSource.chat") or _evo_value(key, "remoteJid", "remoteJID")
    message_id = _evo_value(info, "ID", "id") or _evo_value(key, "id")
    if not jid or not message_id:
        return None
    text = _evo_value(message, "conversation", "extendedTextMessage.text", "imageMessage.caption",
                      "videoMessage.caption", "documentMessage.caption", "buttonsResponseMessage.selectedDisplayText",
                      "listResponseMessage.title") or ""
    stamp = _evo_value(info, "Timestamp", "timestamp") or data.get("messageTimestamp")
    if isinstance(stamp, (int, float)):
        stamp = datetime.fromtimestamp(stamp, timezone.utc).isoformat()
    elif isinstance(stamp, str) and stamp.isdigit():
        stamp = datetime.fromtimestamp(int(stamp), timezone.utc).isoformat()
    elif not isinstance(stamp, str):
        stamp = datetime.now(timezone.utc).isoformat()
    instance = str(raw.get("instanceName") or raw.get("instanceId") or raw.get("instance") or "")
    if not instance:
        return None
    from_me = _evo_value(info, "IsFromMe", "isFromMe", "MessageSource.IsFromMe", "messageSource.isFromMe")
    if from_me is None:
        from_me = key.get("fromMe", False)
    message_type = _evo_value(info, "Type", "type") or data.get("messageType") or "text"
    return {
        "provider": "evolution_go", "instance": instance,
        "event_id": hashlib.sha256(f"{instance}:{message_id}".encode()).hexdigest(),
        "message_id": str(message_id), "remote_jid": str(jid),
        "remote_jid_alt": _evo_value(info, "SenderAlt", "senderAlt") or _evo_value(key, "remoteJidAlt"),
        "participant_alt": _evo_value(info, "ParticipantAlt", "participantAlt") or _evo_value(key, "participant"),
        "from_me": bool(from_me),
        "message_type": str(message_type),
        "text": str(text)[:10000], "timestamp": stamp,
        "raw_type": str(message_type),
    }


def create_whatsapp_inbound_router(get_db, company_key, valid_companies, require_permission, sender=None):
    router = APIRouter()

    @router.post("/internal/whatsapp/events")
    async def receive_event(request: Request, x_whatsapp_inbound_token: str = Header("")):
        _require_local_request(request)
        settings = inbound_settings()
        if not settings["token"] or not settings["instance"] or settings["company"] not in valid_companies:
            logger.error("Canal WhatsApp interno sem configuracao completa.")
            raise HTTPException(503, "Canal interno nao configurado.")
        if not hmac.compare_digest(x_whatsapp_inbound_token, settings["token"]):
            logger.warning("Autenticacao recusada no canal WhatsApp interno.")
            raise HTTPException(401, "Canal interno nao autorizado.")
        if not settings["enabled"]:
            raise HTTPException(503, "Recebimento WhatsApp desativado.")
        raw = await _read_limited_json(request, settings["max_body"])
        try:
            body = BaileysInboundEvent.model_validate(raw)
        except ValidationError as exc:
            logger.warning("Evento WhatsApp interno invalido: %s", exc.error_count())
            raise HTTPException(422, "Evento WhatsApp invalido.") from exc
        if body.instance != settings["instance"]:
            logger.warning("Instancia WhatsApp interna recusada.")
            raise HTTPException(403, "Instancia nao autorizada.")
        conn = get_db(settings["company"])
        try:
            try:
                result = process_inbound_event(
                    conn, settings["company"], body.model_dump(), sender=sender, outbound=outbound_settings(),
                )
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
        except HTTPException:
            raise
        except Exception:
            logger.exception("Falha ao registrar evento WhatsApp interno.")
            raise
        finally:
            conn.close()
        status_code = 200 if result["status"] == "processado" or result["duplicate"] else 202
        return JSONResponse(status_code=status_code, content=result)

    @router.post("/api/whatsapp/evolution-go/webhook/{secret}")
    async def receive_evolution_go_event(secret: str, request: Request):
        if len(secret) < 32:
            raise HTTPException(404, "Webhook não encontrado.")
        raw = await _read_limited_json(request, 262144)
        match = None
        for company in valid_companies:
            conn = get_db(company)
            try:
                cfg = {row["key"]: row["value"] for row in conn.execute(
                    "SELECT key,value FROM whatsapp_config WHERE key IN ('provider','instance_id','evolution_go_webhook_secret')"
                ).fetchall()}
            finally:
                conn.close()
            expected = cfg.get("evolution_go_webhook_secret", "")
            if cfg.get("provider") == "evolution_go" and expected and hmac.compare_digest(secret, expected):
                match = (company, cfg.get("instance_id", ""))
                break
        if not match:
            logger.warning("Evolution GO webhook recusado: segredo não reconhecido.")
            raise HTTPException(401, "Webhook não autorizado.")
        event = _normalize_evolution_go(raw)
        if event is None:
            return {"ok": True, "ignored": True}
        company, configured_instance = match
        if configured_instance and event["instance"] != configured_instance:
            raise HTTPException(403, "Instância Evolution GO não autorizada.")
        conn = get_db(company)
        try:
            result = process_inbound_event(conn, company, event, sender=sender, outbound=outbound_settings())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception:
            logger.exception("Falha ao processar webhook Evolution GO.")
            raise
        finally:
            conn.close()
        return JSONResponse(status_code=200 if result["status"] == "processado" or result["duplicate"] else 202, content=result)

    @router.get("/api/whatsapp/inbound-events")
    def inbound_events(limit: int = 100, x_token: str = Header("")):
        require_permission(x_token, "clientes_whatsapp", "view")
        current_company = company_key()
        conn = get_db(current_company)
        try:
            return repository.list_inbound_events(conn, current_company, limit)
        finally:
            conn.close()

    return router
