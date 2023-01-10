import logging
from flask import Response

from grubstack.envelope import GResponse, GStatusCode

logger = logging.getLogger('grubstack')

def gs_make_response(*args, **kwargs):
  xr = GResponse(
    kwargs.get('data') or kwargs.get('fallback'),
    kwargs.get('message') or '',
    kwargs.get('status') or GStatusCode.SUCCESS,
  )

  r = Response(xr.tojson(), status=kwargs.get('httpstatus') or 200,
               headers=kwargs.get('headers'))
  r.headers['Content-Type'] = 'application/json'
  return r
