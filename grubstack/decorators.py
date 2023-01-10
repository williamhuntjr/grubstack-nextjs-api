import logging
from functools import wraps
from flask import request, Response, g
from flask_jwt_extended import get_current_user, verify_jwt_in_request
from . import config
from .utilities import gs_make_response
from .envelope import GStatusCode

logger = logging.getLogger('grubstack')

def query_limit():
  def decorator(func):
    @wraps(func)
    def querylimit(*args, **kwargs):
      tlimit = request.args.get('limit')
      if tlimit is not None and tlimit.isdigit() and int(tlimit) >= 1:
        maxlimit = config.getint('api', 'max_limit', fallback=1000)
        limit = int(tlimit)
        if limit > maxlimit:
          limit = maxlimit
        g.limit = limit
      else:
        g.limit = config.getint('api', 'default_limit', fallback=200)

      offset = request.args.get('offset')
      if offset is not None and offset.isdigit() and int(offset) >= 0:
        g.offset = int(offset)
      else:
        g.offset = 0

      page = request.args.get('page')
      if page is not None and page.isdigit() and int(page) > 0:
        g.page = int(page) - 1 # PostgreSQL is zero-indexed
      else:
        g.page = 0
      return func(*args, **kwargs)
    return querylimit
  return decorator