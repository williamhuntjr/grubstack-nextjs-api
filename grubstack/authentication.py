import json, requests
from six.moves.urllib.request import urlopen
from functools import wraps
from jose import jwt

from flask import request, _request_ctx_stack, session, Blueprint
from .utilities import generate_hash, gs_make_response

from . import app, config, logger, gsdb, coredb

AUTH0_DOMAIN = app.config['AUTH0_DOMAIN']
AUTH0_AUDIENCE = app.config['AUTH0_AUDIENCE']

ALGORITHMS = ["RS256"]

gsauth = Blueprint('auth', __name__)

class AuthError(Exception):
  def __init__(self, error, status_code):
    self.error = error
    self.status_code = status_code

def get_token_auth_header():
  auth = request.headers.get("Authorization", None)
  if not auth:
    raise AuthError({ "code": "authorization_header_missing",
                      "description": "Authorization header is expected" }, 401)

  parts = auth.split()

  if parts[0].lower() != "bearer":
    raise AuthError({ "code": "invalid_header",
                      "description": "Authorization header must start with Bearer" }, 401)
  elif len(parts) == 1:
    raise AuthError({ "code": "invalid_header",
                      "description": "Token not found" }, 401)
  elif len(parts) > 2:
    raise AuthError({ "code": "invalid_header",
                      "description": "Authorization header must be Bearer token" }, 401)
  token = parts[1]
  return token

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    token = get_token_auth_header()
    jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks["keys"]:
      if key["kid"] == unverified_header["kid"]:
        rsa_key = {
          "kty": key["kty"],
          "kid": key["kid"],
          "use": key["use"],
          "n": key["n"],
          "e": key["e"]
        }
    if rsa_key:
      try:
        payload = jwt.decode(
          token,
          rsa_key,
          algorithms=ALGORITHMS,
          audience=AUTH0_AUDIENCE,
          issuer="https://"+AUTH0_DOMAIN+"/"
        )
      except jwt.ExpiredSignatureError:
        raise AuthError({ "code": "token_expired",
                          "description": "token is expired" }, 401)
      except jwt.JWTClaimsError:
        raise AuthError({ "code": "invalid_claims",
                          "description": "incorrect claims, please check the audience and issuer" }, 401)
      except Exception:
        raise AuthError({ "code": "invalid_header",
                          "description": "Unable to parse authentication token." }, 401)

      _request_ctx_stack.top.current_user = payload

      return f(*args, **kwargs)
    raise AuthError({ "code": "invalid_header",
                      "description": "Unable to find appropriate key" }, 401)
  return decorated

def requires_scope(required_scope):
  def decorator(func):
    @wraps(func)
    def scope_required(*args, **kwargs):
      token = get_token_auth_header()
      unverified_claims = jwt.get_unverified_claims(token)
      if config.getboolean('logging', 'log_requests'):
        logger.info(f"[user:{'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
      if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
          if token_scope == required_scope:
            return func(*args, **kwargs)
      body = request.get_data().decode('utf-8')
      raise AuthError({ "code": "Unauthorized",
                        "description": "You don't have access to this resource" }, 403)
    return scope_required
  return decorator

def get_user_info():
  current_user = _request_ctx_stack.top.current_user
  return current_user

def get_user_id():
  current_user = get_user_info()
  return current_user['sub'] if 'sub' in current_user else None

def get_tenant_id():
  current_user = get_user_info()
  if 'sub' in current_user:
    row = gsdb.fetchone("SELECT tenant_id FROM gs_user_tenant WHERE user_id = %s AND is_owner = 't'", (current_user['sub'],))
    if row:
      return row['tenant_id']
    else:
      slug = generate_hash()
      access_token = generate_hash()
      qry = coredb.execute("INSERT INTO gs_tenant VALUES (DEFAULT, 'f', 't', %s, %s)", (slug, access_token,))
      row = coredb.fetchone("SELECT tenant_id FROM gs_tenant WHERE slug = %s", (slug,))
      qry = gsdb.execute("INSERT INTO gs_user_tenant VALUES (%s, %s, 't')", (current_user['sub'], row['tenant_id'],))
      return row['tenant_id']
  return None

def get_tenant_slug():
  current_user = get_user_info()
  if 'sub' in current_user:
    row = gsdb.fetchone("SELECT tenant_id FROM gs_user_tenant WHERE user_id = %s AND is_owner = 't'", (current_user['sub'],))
    if row:
      tenant_id = row['tenant_id']
      slug = coredb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
      return slug[0]
  return None

@gsauth.route('/auth/userinfo', methods=['GET'])
@requires_auth
def get_userinfo():
  token = get_token_auth_header()
  jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
  jwks = json.loads(jsonurl.read())
  unverified_header = jwt.get_unverified_header(token)
  rsa_key = {}
  for key in jwks["keys"]:
    if key["kid"] == unverified_header["kid"]:
      rsa_key = {
        "kty": key["kty"],
        "kid": key["kid"],
        "use": key["use"],
        "n": key["n"],
        "e": key["e"]
      }
  if rsa_key:
    try:
      payload = jwt.decode(
        token,
        rsa_key,
        algorithms=ALGORITHMS,
        audience=AUTH0_AUDIENCE,
        issuer="https://"+AUTH0_DOMAIN+"/"
      )
    except jwt.ExpiredSignatureError:
      raise AuthError({ "code": "token_expired",
                        "description": "token is expired" }, 401)
    except jwt.JWTClaimsError:
      raise AuthError({ "code": "invalid_claims",
                        "description":"incorrect claims, please check the audience and issuer" }, 401)
    except Exception:
      raise AuthError({ "code": "invalid_header",
                        "description":"Unable to parse authentication token. "}, 401)

    resp = requests.get("https://"+AUTH0_DOMAIN+"/userinfo", headers={'Authorization': 'Bearer '+token})
    json_data = resp.json()
    
    return gs_make_response(data=json_data)
  raise AuthError({"code": "invalid_header",
        "description": "Unable to find appropriate key"}, 401)

app.register_blueprint(gsauth, url_prefix=config.get('general', 'urlprefix', fallback='/'))
