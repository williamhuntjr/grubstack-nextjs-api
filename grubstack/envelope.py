import json
from enum import Enum

class GStatusCode(Enum):
  SUCCESS = 'success'
  WARNING = 'warning'
  ERROR   = 'error'
  UNKNOWN = 'unknown'

  def __str__(self):
    return self.value

class GStatus(dict):
  def __init__(self, code=GStatusCode.SUCCESS, message=str()):
    dict.__init__(self)
    self['code'] = code
    self['message'] = message

class GRequest(dict):
  def __init__(self, data=None, options=dict()):
    dict.__init__(self)
    self['data'] = data
    self['options'] = options

  def __str__(self):
    return self.tojson()

  def tojson(self):
    return json.dumps(self, indent=2, default=str)

  @staticmethod
  def fromjson(pjson):
    pdict = json.loads(pjson)
    if 'data' not in pdict:
      raise ValueError('Missing data object')
    if type(pdict['data']) != type(dict()) and type(pdict['data']) != type(list()):
      raise TypeError('Invalid data object. Must be a JSON Object or Array')
    return GRequest(
      pdict['data'],
      pdict.get('options')
    )

class GResponse(dict):
  def __init__(self, data=str(), message=str(), status=GStatusCode.SUCCESS):
    dict.__init__(self)
    self['data'] = data
    self['status'] = GStatus(status, message)

  def __str__(self):
    return self.tojson()

  def tojson(self):
    return json.dumps(self, indent=2, default=str)

  @staticmethod
  def fromjson(pjson):
    pdict = json.loads(pjson)
    if 'data' not in pdict:
      raise ValueError('Missing data object')
    if 'status' not in pdict:
      raise ValueError('Missing status object')

    return GResponse(
      pdict['data'],
      pdict['status']['message'],
      GStatusCode[pdict['status']['code'].upper()],
    )