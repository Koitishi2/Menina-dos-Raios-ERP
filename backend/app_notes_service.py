try:
    from .utils import _normalize_name
except ImportError:
    from utils import _normalize_name


def app_note_dict_from_row(
    conn,
    row,
    catalog_prices=None,
    normalize_name_func=None,
):
    normalize_name = normalize_name_func or _normalize_name
    note = dict(row)
    catalog_prices = catalog_prices or {}
    note["items"] = [dict(r) for r in conn.execute(
        "SELECT id,product,quantity,quantity_provided,weight,unit,unit_price,price_provided,position FROM app_note_items WHERE note_id=? ORDER BY position,id",
        (row["id"],)).fetchall()]
    effective_total = 0.0
    for item in note["items"]:
        provided = bool(item.get("price_provided"))
        catalog_price = catalog_prices.get(normalize_name(item.get("product") or ""))
        has_catalog = catalog_price is not None
        effective = float(item.get("unit_price") or 0) if provided else (float(catalog_price) if has_catalog else 0.0)
        item["effective_unit_price"] = effective
        item["effective_price_provided"] = bool(provided or has_catalog)
        item["price_from_catalog"] = bool(not provided and has_catalog)
        if item["effective_price_provided"]: effective_total += float(item.get("weight") or 0) * effective
    note["total"] = round(effective_total, 2)
    return note
