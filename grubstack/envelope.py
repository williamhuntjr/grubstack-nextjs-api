import json
from enum import Enum

class GStatusCode(Enum):
  """Enum containing statuses in string format"""
  SUCCESS = 'success'
  WARNING = 'warning'
  ERROR   = 'error'
  UNKNOWN = 'unknown'

  def __str__(self):
    return self.value

class GStatus(dict):
  """A dict representing the status of a response from the API"""
  def __init__(self, code=GStatusCode.SUCCESS, message=str()):
    dict.__init__(self)
    self['code'] = code
    self['message'] = message

class GRequest(dict):
  """A dict representing a request to the API"""
  def __init__(self, data=None, options=dict()):
    dict.__init__(self)
    self['data'] = data
    self['options'] = options

  def __str__(self):
    """Used anytime a string representation is needed, such as when print()'ing"""
    return self.tojson()

  def tojson(self):
    """Serialize current GRequest object to JSON"""
    return json.dumps(self, indent=2, default=str)

  @staticmethod
  def fromjson(pjson):
    """Create GRequest object from provided JSON."""
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
  """A dict representing a response from the API"""
  def __init__(self, data=str(), message=str(), status=GStatusCode.SUCCESS):
    dict.__init__(self)
    self['data'] = data
    self['status'] = GStatus(status, message)

  def __str__(self):
    """Used anytime a string representation is needed, such as when print()'ing"""
    return self.tojson()

  def tojson(self):
    """Serialize current GResponse object to JSON"""
    return json.dumps(self, indent=2, default=str)

  @staticmethod
  def fromjson(pjson):
    """Create GResponse object from provided JSON."""
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