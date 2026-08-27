from typing import Optional


class QuoteItemsLimitError(Exception):
    pass


def _quote_companies():
    return {
        "estrada":{
            "key":"estrada",
            "cnpj":"63.585.166/0001-37",
            "razao_social":"J. M. de Lima",
            "nome_fantasia":"Menina da Estrada",
            "endereco":"Rua Raimundo Alves de Souza, 205 - Jardim Tropical, Boa Vista - Roraima - Brasil",
            "cep":"69314-670",
            "email":"adrianoabreub@gmail.com",
            "whatsapp":"+55 (21) 98426-1686 / (95) 99123-3960",
            "logo":"/assets/menina-estrada-logo.png"
        },
        "raios":{
            "key":"raios",
            "cnpj":"45.783.879/0001-23",
            "razao_social":"Menina dos Raios LTDA",
            "nome_fantasia":"Menina dos Raios",
            "endereco":"Rua Raimundo Alves de Souza, 205 - Jardim Tropical, Boa Vista - Roraima - Brasil",
            "cep":"69314-670",
            "email":"meninadosraios@gmail.com",
            "whatsapp":"+55 (95) 99123-3960 / (21) 98426-1686",
            "logo":"/assets/menina-dos-raios-logo.png"
        }
    }


def _quote_company(key:Optional[str]=None):
    companies=_quote_companies()
    return companies.get((key or "estrada").strip().lower(), companies["estrada"])


def quote_totals_from_items(items, discount=0):
    if len(items or []) > 20:
        raise QuoteItemsLimitError()
    subtotal=0.0
    normalized=[]
    for i,it in enumerate(items or [],1):
        qty=float(it.get("quantity") or 0)
        unit_price=float(it.get("unit_price") or 0)
        item_discount=float(it.get("discount") or 0)
        manual_subtotal=it.get("subtotal_override")
        if manual_subtotal is None or manual_subtotal == "":
            line=max(qty*unit_price-item_discount,0)
        else:
            line=max(float(manual_subtotal),0)
        row=dict(it)
        row["item_order"]=int(row.get("item_order") or i)
        row["quantity"]=qty
        row["unit_price"]=unit_price
        row["discount"]=item_discount
        row["subtotal"]=line
        row["unit"]=str(row.get("unit") or "UND").upper()
        row["description"]=str(row.get("description") or "").strip()
        subtotal+=line
        normalized.append(row)
    disc=max(float(discount or 0),0)
    return normalized, subtotal, max(subtotal-disc,0)
