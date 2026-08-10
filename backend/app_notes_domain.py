from fastapi import HTTPException


def _clean_app_note(body: dict):
    client=str(body.get("client") or "").strip()[:120]
    note_date=str(body.get("date") or body.get("note_date") or "").strip()[:20]
    raw_items=body.get("items") or []
    if not isinstance(raw_items,list) or len(raw_items)>100:
        raise HTTPException(400,"Lista de itens invÃ¡lida (mÃ¡ximo 100).")
    items=[]; total=0.0
    for pos,raw in enumerate(raw_items):
        if not isinstance(raw,dict): continue
        product=str(raw.get("product") or "").strip()[:160]
        unit=str(raw.get("unit") or "").strip()[:20]
        quantity_provided=raw.get("quantity") is not None and str(raw.get("quantity")).strip()!=""
        price_raw=raw.get("unit_price") if raw.get("unit_price") is not None else raw.get("price")
        price_provided=price_raw is not None and str(price_raw).strip()!=""
        try:
            quantity=float(raw.get("quantity")) if quantity_provided else 0.0
            weight=float(raw.get("weight") if raw.get("weight") is not None else quantity)
            price=float(price_raw) if price_provided else 0.0
        except Exception: raise HTTPException(400,"Quantidade ou preÃ§o invÃ¡lido.")
        if abs(quantity)>100000000 or abs(weight)>100000000 or abs(price)>100000000: raise HTTPException(400,"Valor fora do limite permitido.")
        items.append({"product":product,"quantity":quantity,"quantity_provided":quantity_provided,
                      "weight":weight,"unit":unit,"unit_price":price,"price_provided":price_provided,"position":pos})
        if price_provided: total+=weight*price
    return client,note_date,items,round(total,2)
