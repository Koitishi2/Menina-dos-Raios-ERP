def company_key_from(value, company_dbs):
    key=str(value or "").strip().lower()
    return key if key in company_dbs else "raios"


def company_db_path_for(value, company_dbs, db_path):
    return company_dbs.get(company_key_from(value, company_dbs), db_path)
