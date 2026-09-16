import sqlite3

try:
    from ..domains.sellers import clean_seller_name, normalize_seller_name
    from ..repositories import sellers_repository as repository
except ImportError:
    from domains.sellers import clean_seller_name, normalize_seller_name
    from repositories import sellers_repository as repository


def list_sellers(conn, company_key, include_inactive=False, search=""):
    return repository.list_sellers(conn, company_key, include_inactive, search)


def similar_sellers(conn, company_key, name):
    try:
        clean = clean_seller_name(name)
    except ValueError:
        return []
    pieces = [p for p in clean.split(" ") if len(p) >= 3]
    rows = repository.list_sellers(conn, company_key, include_inactive=True)
    if not pieces:
        return rows[:10]
    matches = []
    for row in rows:
        hay = row["name"].casefold()
        score = sum(1 for piece in pieces if piece.casefold() in hay)
        if score:
            item = dict(row)
            item["score"] = score
            matches.append(item)
    matches.sort(key=lambda r: (-r["score"], r["name"].casefold()))
    return matches[:10]


def create_seller(conn, company_key, name, username):
    clean = clean_seller_name(name)
    normalized = normalize_seller_name(clean)
    existing = repository.find_by_normalized(conn, company_key, normalized)
    if existing:
        return existing, True
    try:
        return repository.create_seller(conn, company_key, clean, normalized, username), False
    except sqlite3.IntegrityError:
        existing = repository.find_by_normalized(conn, company_key, normalized)
        if existing:
            return existing, True
        raise


def update_seller(conn, company_key, seller_id, name, username, reason=""):
    clean = clean_seller_name(name)
    normalized = normalize_seller_name(clean)
    current = repository.find_by_id(conn, company_key, seller_id)
    if not current:
        return None
    existing = repository.find_by_normalized(conn, company_key, normalized)
    if existing and existing["id"] != seller_id:
        raise sqlite3.IntegrityError("duplicate seller name")
    return repository.update_seller_name(conn, company_key, seller_id, clean, normalized, username, reason)


def require_active_seller(conn, company_key, seller_id):
    seller = repository.find_by_id(conn, company_key, seller_id)
    if not seller:
        raise ValueError("Vendedor nao encontrado.")
    if not int(seller.get("active") or 0):
        raise ValueError("Vendedor inativo.")
    return seller
