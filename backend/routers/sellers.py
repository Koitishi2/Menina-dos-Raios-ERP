import sqlite3

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

try:
    from ..repositories import sellers_repository as repository
    from ..services import sellers_service as service
except ImportError:
    from repositories import sellers_repository as repository
    from services import sellers_service as service


class SellerIn(BaseModel):
    name: str
    reason: str = ""


def create_sellers_router(get_db, company_key, require_permission):
    router = APIRouter()

    def authorized(token, action="view", module_context=""):
        return require_permission(token, "vendedores", action, company_key(), module_context)

    @router.get("/api/sellers")
    def sellers(search: str = "", include_inactive: int = 0, module_context: str = "", x_token: str = Header("")):
        authorized(x_token, "view", module_context)
        conn = get_db()
        try:
            return service.list_sellers(conn, company_key(), bool(include_inactive), search)
        finally:
            conn.close()

    @router.get("/api/sellers/similar")
    def similar(name: str = "", module_context: str = "", x_token: str = Header("")):
        authorized(x_token, "view", module_context)
        conn = get_db()
        try:
            return service.similar_sellers(conn, company_key(), name)
        finally:
            conn.close()

    @router.post("/api/sellers")
    def create(body: SellerIn, module_context: str = "", x_token: str = Header("")):
        sess = authorized(x_token, "create", module_context)
        conn = get_db()
        try:
            seller, existed = service.create_seller(conn, company_key(), body.name, sess.get("username", ""))
            conn.commit()
            return {"seller": seller, "existed": existed}
        except ValueError as exc:
            conn.rollback()
            raise HTTPException(400, str(exc))
        except sqlite3.IntegrityError:
            conn.rollback()
            raise HTTPException(409, "Vendedor ja cadastrado.")
        finally:
            conn.close()

    @router.put("/api/sellers/{seller_id}")
    def update(seller_id: str, body: SellerIn, module_context: str = "", x_token: str = Header("")):
        sess = authorized(x_token, "edit", module_context)
        conn = get_db()
        try:
            seller = service.update_seller(
                conn, company_key(), seller_id, body.name, sess.get("username", ""), body.reason
            )
            if not seller:
                raise HTTPException(404, "Vendedor nao encontrado.")
            conn.commit()
            return seller
        except HTTPException:
            conn.rollback()
            raise
        except ValueError as exc:
            conn.rollback()
            raise HTTPException(400, str(exc))
        except sqlite3.IntegrityError:
            conn.rollback()
            raise HTTPException(409, "Ja existe vendedor equivalente nesta empresa.")
        finally:
            conn.close()

    @router.post("/api/sellers/{seller_id}/activate")
    def activate(seller_id: str, module_context: str = "", x_token: str = Header("")):
        sess = authorized(x_token, "edit", module_context)
        conn = get_db()
        try:
            seller = repository.set_active(conn, company_key(), seller_id, True, sess.get("username", ""))
            if not seller:
                raise HTTPException(404, "Vendedor nao encontrado.")
            conn.commit()
            return seller
        finally:
            conn.close()

    @router.post("/api/sellers/{seller_id}/deactivate")
    def deactivate(seller_id: str, module_context: str = "", x_token: str = Header("")):
        sess = authorized(x_token, "edit", module_context)
        conn = get_db()
        try:
            seller = repository.set_active(conn, company_key(), seller_id, False, sess.get("username", ""))
            if not seller:
                raise HTTPException(404, "Vendedor nao encontrado.")
            conn.commit()
            return seller
        finally:
            conn.close()

    @router.get("/api/sellers/{seller_id}/history")
    def history(seller_id: str, module_context: str = "", x_token: str = Header("")):
        authorized(x_token, "view", module_context)
        conn = get_db()
        try:
            if not repository.find_by_id(conn, company_key(), seller_id):
                raise HTTPException(404, "Vendedor nao encontrado.")
            return repository.seller_history(conn, company_key(), seller_id)
        finally:
            conn.close()

    return router
