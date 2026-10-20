import time
from functools import lru_cache

@lru_cache(maxsize=1)
def _get_whatsapp_config_cached(cache_buster: int):
    # This acts as our cached db read
    # cache_buster will be something like time.time() // 60 for a 60s cache
    return {"data": "from_db"}

def get_whatsapp_config():
    # Cache for 10 seconds
    return _get_whatsapp_config_cached(int(time.time() / 10))

print(get_whatsapp_config())
print(_get_whatsapp_config_cached.cache_info())
