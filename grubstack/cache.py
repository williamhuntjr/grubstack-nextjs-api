import json
from flask_caching import Cache

from . import app, config

cacheconfig = json.loads(config.get('caching', 'config', fallback='{"CACHE_TYPE": "null"}'))
cache = Cache(app, config=cacheconfig)

def cachekey(*args, **kwargs) -> str:
  return ''.join(args)

def clearcaches(caches: list) -> None:
  cache.delete_many(*caches)
  caches.clear()
