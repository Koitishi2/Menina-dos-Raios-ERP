import timeit
import sqlite3
import random

def test_db_read():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE whatsapp_config (key TEXT PRIMARY KEY, value TEXT)')

    # insert some random keys
    for i in range(20):
        conn.execute('INSERT INTO whatsapp_config VALUES (?, ?)', (f'key_{i}', f'val_{i}'))

    def get_cfg_no_cache():
        return {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM whatsapp_config").fetchall()}


    from functools import lru_cache

    @lru_cache(maxsize=1)
    def get_cfg_with_cache():
        return {r["key"]:r["value"] for r in conn.execute("SELECT key,value FROM whatsapp_config").fetchall()}

    # cache warmup
    get_cfg_with_cache()

    time_no_cache = timeit.timeit(stmt='get_cfg_no_cache()', globals=locals(), number=1000)
    time_with_cache = timeit.timeit(stmt='get_cfg_with_cache()', globals=locals(), number=1000)

    print(f"Time without cache: {time_no_cache:.6f} s")
    print(f"Time with cache: {time_with_cache:.6f} s")
    print(f"Improvement: {(time_no_cache - time_with_cache) / time_no_cache * 100:.2f}%")

if __name__ == '__main__':
    test_db_read()
