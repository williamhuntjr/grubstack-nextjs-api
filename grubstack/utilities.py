import random

from flask import Response

from grubstack.envelope import GResponse, GStatusCode

def gs_make_response(*args, **kwargs):
  xr = GResponse(
    kwargs.get('data') or kwargs.get('fallback'),
    kwargs.get('message') or '',
    kwargs.get('status') or GStatusCode.SUCCESS,
    kwargs.get('totalrowcount') or '',
    kwargs.get('totalpages') or '',
  )

  r = Response(xr.tojson(), status=kwargs.get('httpstatus') or 200,
               headers=kwargs.get('headers'))
  r.headers['Content-Type'] = 'application/json'
  return r

def generate_hash(num: int = 12):
  string = []
  chars = 'abcdefghijklmnopqrstuvwxyz1234567890'
  for k in range(1, num+1):
    string.append(random.choice(chars))
  string = "".join(string)
  return string