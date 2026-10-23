import os

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from ..repositories import whatsapp_repository as repository
    from ..services.whatsapp_campaign_service import (
        cancel_manual_batch, confirm_manual_batch, create_manual_batch,
        list_suggestions, send_manual_batch,
    )
except ImportError:
    from repositories import whatsapp_repository as repository
    from services.whatsapp_campaign_service import (
        cancel_manual_batch, confirm_manual_batch, create_manual_batch,
        list_suggestions, send_manual_batch,
    )


TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


class ManualBatchIn(BaseModel):
    client_ids: list[str] = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    filters: dict = Field(default_factory=dict)
    request_id: str | None = Field(default=None, min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")


def outbound_settings():
    mode = os.environ.get("WHATSAPP_OUTBOUND_MODE", "disabled").strip().lower()
    if mode not in ("disabled", "sandbox", "production"):
        mode = "disabled"
    raw_numbers = os.environ.get("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "")
    numbers = {"+" + "".join(char for char in item if char.isdigit()) for item in raw_numbers.split(",") if item.strip()}
    return {
        "enabled": os.environ.get("WHATSAPP_OUTBOUND_ENABLED", "false").strip().lower() in TRUE_VALUES,
        "mode": mode,
        "production_approved": os.environ.get("WHATSAPP_OUTBOUND_PRODUCTION_APPROVED", "false").strip().lower() in TRUE_VALUES,
        "sandbox_numbers": numbers,
        "dedupe_days": max(1, min(int(os.environ.get("WHATSAPP_OUTBOUND_DEDUPE_DAYS", "7")), 90)),
    }


def create_whatsapp_campaigns_router(get_db, company_key, require_permission, sender):
    router = APIRouter()

    def _handle_error(exc):
        if isinstance(exc, LookupError):
            raise HTTPException(404, str(exc)) from exc
        if isinstance(exc, PermissionError):
            raise HTTPException(403, str(exc)) from exc
        raise HTTPException(400, str(exc)) from exc

    @router.get("/api/whatsapp/suggestions")
    def suggestions(
        minimum_days: int = Query(8, ge=0, le=3650),
        include_blocked: bool = False,
        selectable_only: bool = False,
        phone_valid: bool | None = None,
        consent: str | None = None,
        open_conversation: bool | None = None,
        pending_order: bool | None = None,
        x_token: str = Header(""),
    ):
        require_permission(x_token, "clientes_whatsapp_sugestoes", "view")
        conn = get_db()
        try:
            return list_suggestions(conn, company_key(), {
                "minimum_days": minimum_days, "include_blocked": include_blocked,
                "selectable_only": selectable_only, "phone_valid": phone_valid,
                "consent": consent, "open_conversation": open_conversation,
                "pending_order": pending_order,
            })
        finally:
            conn.close()

    @router.get("/api/whatsapp/manual-batches")
    def batches(x_token: str = Header("")):
        require_permission(x_token, "clientes_whatsapp_lotes", "view")
        conn = get_db()
        try:
            return repository.list_manual_batches(conn, company_key())
        finally:
            conn.close()

    @router.get("/api/whatsapp/manual-batches/{batch_id}")
    def batch(batch_id: str, x_token: str = Header("")):
        require_permission(x_token, "clientes_whatsapp_lotes", "view")
        conn = get_db()
        try:
            result = repository.get_manual_batch(conn, company_key(), batch_id)
            if not result:
                raise HTTPException(404, "lote_nao_encontrado")
            return result
        finally:
            conn.close()

    @router.post("/api/whatsapp/manual-batches")
    def create_batch(body: ManualBatchIn, x_token: str = Header("")):
        user = require_permission(x_token, "clientes_whatsapp_lotes", "create")
        conn = get_db()
        try:
            try:
                return create_manual_batch(
                    conn, company_key(), user["username"], body.client_ids,
                    body.message, body.filters, request_id=body.request_id,
                )
            except (ValueError, LookupError, PermissionError) as exc:
                _handle_error(exc)
        finally:
            conn.close()

    @router.post("/api/whatsapp/manual-batches/{batch_id}/confirm")
    def confirm_batch(batch_id: str, x_token: str = Header("")):
        user = require_permission(x_token, "clientes_whatsapp_lotes", "approve")
        conn = get_db()
        try:
            try:
                return confirm_manual_batch(conn, company_key(), batch_id, user["username"])
            except (ValueError, LookupError, PermissionError) as exc:
                _handle_error(exc)
        finally:
            conn.close()

    @router.post("/api/whatsapp/manual-batches/{batch_id}/cancel")
    def cancel_batch(batch_id: str, x_token: str = Header("")):
        user = require_permission(x_token, "clientes_whatsapp_lotes", "edit")
        conn = get_db()
        try:
            try:
                return cancel_manual_batch(conn, company_key(), batch_id, user["username"])
            except (ValueError, LookupError, PermissionError) as exc:
                _handle_error(exc)
        finally:
            conn.close()

    @router.post("/api/whatsapp/manual-batches/{batch_id}/send")
    def send_batch(batch_id: str, x_token: str = Header("")):
        user = require_permission(x_token, "clientes_whatsapp_envio", "create")
        conn = get_db()
        try:
            config = {row["key"]: row["value"] for row in conn.execute("SELECT key,value FROM whatsapp_config").fetchall()}
            try:
                return send_manual_batch(
                    conn, company_key(), batch_id, user["username"], outbound_settings(), config, sender,
                )
            except (ValueError, LookupError, PermissionError) as exc:
                _handle_error(exc)
        finally:
            conn.close()

    return router
