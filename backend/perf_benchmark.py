import timeit
import sqlite3

setup_baseline = '''
import sqlite3

def init_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE whatsapp_config (key TEXT PRIMARY KEY, value TEXT)")
    for i in range(20):
        conn.execute("INSERT INTO whatsapp_config VALUES (?, ?)", (f"key_{i}", f"val_{i}"))
    return conn

conn = init_db()

def get_no_cache():
    return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM whatsapp_config").fetchall()}
'''

code_baseline = "get_no_cache()"

setup_optimized = '''
import sqlite3
from functools import lru_cache

def init_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE whatsapp_config (key TEXT PRIMARY KEY, value TEXT)")
    for i in range(20):
        conn.execute("INSERT INTO whatsapp_config VALUES (?, ?)", (f"key_{i}", f"val_{i}"))
    return conn

conn = init_db()

@lru_cache(maxsize=32)
def _wa_config_cached(company: str):
    rows = conn.execute("SELECT key, value FROM whatsapp_config").fetchall()
    return {r["key"]: r["value"] for r in rows}

def get_wa_config_cached():
    return dict(_wa_config_cached("raios"))

# warmup
get_wa_config_cached()
'''

code_optimized = "get_wa_config_cached()"

N = 10000

time_baseline = timeit.timeit(stmt=code_baseline, setup=setup_baseline, number=N)
time_optimized = timeit.timeit(stmt=code_optimized, setup=setup_optimized, number=N)

print("⚡ WhatsApp Config Benchmark ⚡")
print(f"Iterations: {N}")
print(f"Baseline Time:  {time_baseline:.4f}s")
print(f"Optimized Time: {time_optimized:.4f}s")
if time_baseline > 0:
    improvement = (time_baseline - time_optimized) / time_baseline * 100
    print(f"Improvement:    {improvement:.2f}%")
