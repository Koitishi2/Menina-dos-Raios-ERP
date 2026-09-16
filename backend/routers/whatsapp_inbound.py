import hmac
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

try:
    from ..repositories import whatsapp_repository as repository
    from ..services.whatsapp_inbound_service import process_inbound_event
except ImportError:
    from repositories import whatsapp_repository as repository
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


def create_whatsapp_inbound_router(get_db, company_key, valid_companies, require_permission):
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
                result = process_inbound_event(conn, settings["company"], body.model_dump())
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
