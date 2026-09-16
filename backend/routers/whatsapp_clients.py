from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from ..repositories import whatsapp_repository as repository
    from .whatsapp_inbound import inbound_settings
    from .whatsapp_campaigns import outbound_settings
    from ..services.whatsapp_order_service import create_damage, register_incoming_message, save_consumption
except ImportError:
    from repositories import whatsapp_repository as repository
    from routers.whatsapp_inbound import inbound_settings
    from routers.whatsapp_campaigns import outbound_settings
    from services.whatsapp_order_service import create_damage, register_incoming_message, save_consumption


class ConsumptionIn(BaseModel):
    product_key: str = Field(min_length=1, max_length=100)
    average_consumption: object
    maximum_consumption: Optional[object] = None
    unit: str = Field(min_length=1, max_length=20)


class DamageIn(BaseModel):
    product_key: str = Field(min_length=1, max_length=100)
    quantity: object
    replacement_percent: object = 0
    reason: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=2000)


class IncomingMessageIn(BaseModel):
    instance_key: str = Field(min_length=1, max_length=100)
    external_message_id: str = Field(min_length=1, max_length=255)
    jid: str = Field(min_length=1, max_length=255)
    received_at: Optional[str] = Field(default=None, max_length=64)
    text: str = Field(default="", max_length=10000)
    event_hash: str = Field(min_length=1, max_length=128)


def create_whatsapp_clients_router(get_db, company_key, require_permission):
    router = APIRouter()

    def authorized(token, module, action="view"):
        return require_permission(token, module, action)

    @router.get("/api/whatsapp/status")
    def status(x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        def can(module, action):
            try:
                authorized(x_token, module, action)
                return True
            except HTTPException:
                return False
        conn = get_db()
        try:
            counts = {
                "conversations": conn.execute("SELECT COUNT(*) FROM whatsapp_conversations WHERE company_key=?", (company_key(),)).fetchone()[0],
                "messages": conn.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE company_key=?", (company_key(),)).fetchone()[0],
                "orders": conn.execute("SELECT COUNT(*) FROM whatsapp_order_drafts WHERE company_key=?", (company_key(),)).fetchone()[0],
                "inbound_events": conn.execute("SELECT COUNT(*) FROM whatsapp_inbound_events WHERE company_key=?", (company_key(),)).fetchone()[0],
                "inbound_attention": conn.execute(
                    "SELECT COUNT(*) FROM whatsapp_inbound_events WHERE company_key=? AND processing_status<>'processado'",
                    (company_key(),),
                ).fetchone()[0],
            }
            settings = inbound_settings()
            outbound = outbound_settings()
            return {
                "mode": "receive_only" if settings["enabled"] else "inbound_disabled",
                "inbound_enabled": settings["enabled"],
                "inbound_configured": bool(settings["token"] and settings["instance"] and settings["company"]),
                "outbound_enabled": outbound["enabled"],
                "outbound_mode": outbound["mode"],
                "sending_enabled": False,
                "conversion_enabled": False,
                "capabilities": {
                    "view_suggestions": can("clientes_whatsapp_sugestoes", "view"),
                    "create_manual_batch": can("clientes_whatsapp_lotes", "create"),
                    "send_manual": can("clientes_whatsapp_envio", "create"),
                },
                "counts": counts,
            }
        finally:
            conn.close()

    @router.get("/api/clients/{client_id}/whatsapp")
    def client_whatsapp(client_id: str, x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        conn = get_db()
        try:
            result = repository.client_whatsapp_summary(conn, company_key(), client_id)
            if not result:
                raise HTTPException(404, "Cliente nao encontrado.")
            return result
        finally:
            conn.close()

    @router.get("/api/clients/{client_id}/whatsapp/conversations")
    def client_conversations(client_id: str, x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        conn = get_db()
        try:
            if not repository.find_client(conn, client_id):
                raise HTTPException(404, "Cliente nao encontrado.")
            return repository.list_conversations(conn, company_key(), client_id)
        finally:
            conn.close()

    @router.get("/api/whatsapp/conversations")
    def conversations(x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        conn = get_db()
        try:
            return repository.list_conversations(conn, company_key())
        finally:
            conn.close()

    @router.get("/api/whatsapp/conversations/{conversation_id}")
    def conversation(conversation_id: str, x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        conn = get_db()
        try:
            result = repository.get_conversation(conn, company_key(), conversation_id)
            if not result:
                raise HTTPException(404, "Conversa nao encontrada.")
            return result
        finally:
            conn.close()

    @router.get("/api/whatsapp/orders")
    def orders(x_token: str = Header("")):
        authorized(x_token, "clientes_pedidos", "view")
        conn = get_db()
        try:
            return repository.list_orders(conn, company_key())
        finally:
            conn.close()

    @router.get("/api/whatsapp/orders/{order_id}")
    def order(order_id: str, x_token: str = Header("")):
        authorized(x_token, "clientes_pedidos", "view")
        conn = get_db()
        try:
            result = repository.get_order(conn, company_key(), order_id)
            if not result:
                raise HTTPException(404, "Pedido nao encontrado.")
            return result
        finally:
            conn.close()

    @router.get("/api/clients/{client_id}/consumption")
    def consumption(client_id: str, x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        conn = get_db()
        try:
            if not repository.find_client(conn, client_id):
                raise HTTPException(404, "Cliente nao encontrado.")
            return repository.list_consumption(conn, company_key(), client_id)
        finally:
            conn.close()

    @router.put("/api/clients/{client_id}/consumption")
    def update_consumption(client_id: str, body: ConsumptionIn, x_token: str = Header("")):
        user = authorized(x_token, "clientes_whatsapp", "edit")
        conn = get_db()
        try:
            if not repository.find_client(conn, client_id):
                raise HTTPException(404, "Cliente nao encontrado.")
            try:
                row = save_consumption(conn, company_key(), client_id, body.model_dump(), user["username"])
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc
            return dict(row)
        finally:
            conn.close()

    @router.get("/api/clients/{client_id}/damages")
    def damages(client_id: str, x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "view")
        conn = get_db()
        try:
            if not repository.find_client(conn, client_id):
                raise HTTPException(404, "Cliente nao encontrado.")
            return repository.list_damages(conn, company_key(), client_id)
        finally:
            conn.close()

    @router.post("/api/clients/{client_id}/damages")
    def add_damage(client_id: str, body: DamageIn, x_token: str = Header("")):
        user = authorized(x_token, "clientes_whatsapp", "create")
        conn = get_db()
        try:
            if not repository.find_client(conn, client_id):
                raise HTTPException(404, "Cliente nao encontrado.")
            try:
                row = create_damage(conn, company_key(), client_id, body.model_dump(), user["username"])
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc
            return dict(row)
        finally:
            conn.close()

    @router.post("/api/whatsapp/webhooks/incoming")
    def incoming(body: IncomingMessageIn, x_token: str = Header("")):
        authorized(x_token, "clientes_whatsapp", "create")
        conn = get_db()
        try:
            try:
                return register_incoming_message(conn, company_key(), body.model_dump())
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from exc
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc
        finally:
            conn.close()

    return router
