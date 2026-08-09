def _pal_period_where(period, month, year):
    from datetime import datetime, timedelta
    where = []; args = []
    if period == 'quinzenal':
        end = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        where.append("saledate >= ? AND saledate <= ?")
        args.extend([start, end])
    elif period == 'quinzenal_prev':
        end = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
        where.append("saledate >= ? AND saledate <= ?")
        args.extend([start, end])
    else:
        if month:
            where.append("strftime('%m',saledate)=?")
            args.append(month.zfill(2))
        if year:
            where.append("strftime('%Y',saledate)=?")
            args.append(str(year))
    return where, args


def _pay_period_map(period, month, year):
    """Helper: retorna (month, year) a partir do period (quinzenal/mensal/anual).
       Para quinzenal, usa mÃƒÂªs/ano corrente no backend (filtro de vendas usa
       _pal_period_where, mas pagamentos sÃƒÂ£o filtrados por month/year).
       Para mensal/anual, usa month/year fornecidos."""
    from datetime import datetime as _dt
    pm = month or ""
    py = year or ""
    if period == "quinzenal":
        now = _dt.now()
        pm = now.strftime("%m")
        py = now.strftime("%Y")
    return pm.zfill(2) if pm else "", str(py) if py else ""
