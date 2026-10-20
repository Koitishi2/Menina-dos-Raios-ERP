import timeit
import sqlite3
import time

def test_lru_cache():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE whatsapp_config (key TEXT PRIMARY KEY, value TEXT)')

    # insert some random keys
    for i in range(20):
        conn.execute('INSERT INTO whatsapp_config VALUES (?, ?)', (f'key_{i}', f'val_{i}'))

    from functools import lru_cache

    # We can't cache the DB connection object directly because it's passed around, or maybe we can?
    # Better to just use a TTL cache or cache it globally based on time.
    # Wait, the prompt says "a simple @lru_cache or similar caching mechanism to reduce database load."
    # If the user edits the config, how do we invalidate the cache?

    pass
