import time

_store = {}

def get_cached(key, ttl=20):
    now = time.time()
    item = _store.get(key)
    if item and (now - item["time"]) < ttl:
        return item["val"]
    return None

def set_cached(key, val):
    _store[key] = {"val": val, "time": time.time()}

def invalidate_cache(prefix=None):
    global _store
    if not prefix:
        _store.clear()
    else:
        _store = {k: v for k, v in _store.items() if not k.startswith(prefix)}
