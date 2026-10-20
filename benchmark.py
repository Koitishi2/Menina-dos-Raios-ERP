import time
from collections import defaultdict
import random

# Generate mock data
random.seed(42)

def _safe_txt(s, default):
    return s if s else default

vendas = []
for i in range(100000):
    vendas.append({
        "client": f"Client_{random.randint(1, 1000)}",
        "total": random.uniform(10, 1000),
        "saledate": "2023-01-01",
        "nf_number": "123",
        "qty": 1
    })

pags = []
for i in range(50000):
    pags.append({
        "client": f"Client_{random.randint(1, 1000)}",
        "amount": random.uniform(10, 1000),
        "payment_date": "2023-01-01",
        "payment_type": "Cash"
    })

def original_code():
    cli_notas = defaultdict(list); cli_pags = defaultdict(list)
    for v in vendas: cli_notas[_safe_txt(v["client"], "SEM NOME")].append(v)
    for p in pags: cli_pags[_safe_txt(p["client"], "SEM NOME")].append(p)
    todos = sorted(set(list(cli_notas.keys()) + list(cli_pags.keys())))

    parts = []
    for cli in todos:
        nts = cli_notas.get(cli, [])
        pp = cli_pags.get(cli, [])
        total_notas = sum(float(n.get("total") or 0) for n in nts)
        total_pago = sum(float(p.get("amount") or 0) for p in pp)
        saldo = round(total_notas - total_pago, 2)
        parts.append(saldo)

def optimized_code():
    cli_notas = defaultdict(list); cli_pags = defaultdict(list)
    cli_notas_total = defaultdict(float); cli_pags_total = defaultdict(float)
    for v in vendas:
        c = _safe_txt(v["client"], "SEM NOME")
        cli_notas[c].append(v)
        cli_notas_total[c] += float(v.get("total") or 0)
    for p in pags:
        c = _safe_txt(p["client"], "SEM NOME")
        cli_pags[c].append(p)
        cli_pags_total[c] += float(p.get("amount") or 0)
    todos = sorted(set(list(cli_notas.keys()) + list(cli_pags.keys())))

    parts = []
    for cli in todos:
        nts = cli_notas.get(cli, [])
        pp = cli_pags.get(cli, [])
        total_notas = cli_notas_total[cli]
        total_pago = cli_pags_total[cli]
        saldo = round(total_notas - total_pago, 2)
        parts.append(saldo)

t0 = time.time()
original_code()
t1 = time.time()
original_time = t1 - t0
print(f"Original Time: {original_time:.4f}s")

t0 = time.time()
optimized_code()
t1 = time.time()
optimized_time = t1 - t0
print(f"Optimized Time: {optimized_time:.4f}s")
