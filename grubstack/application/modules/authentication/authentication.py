import logging, json, time

from datetime import datetime, timezone, timedelta

from functools import wraps

from pypika import Query, Table, Parameter

from flask import Blueprint, request, Response, jsonify, redirect, make_response
from flask_jwt_extended import (
  create_access_token, 
  decode_token,
  create_refresh_token,
  get_jwt_identity,
  get_current_user, 
  current_user,
  verify_jwt_in_request,
  set_access_cookies,
  set_refresh_cookies,
  get_jwt,
  unset_jwt_cookies
)

from grubstack import app, config, gsdb, jwt
from grubstack.envelope import GStatusCode
from grubstack.user import GSUser
from grubstack.utilities import gs_make_response, generate_hash

from .authentication_service import AuthenticationService

authentication = Blueprint('authentication', __name__)
logger = logging.getLogger('grubstack')

authentication_service = AuthenticationService()

def jwt_required(optional=False, fresh=False, refresh=False, locations=None):
  def decorator(func):
    @wraps(func)
    def jwtrequired(*args, **kwargs):
      verify_jwt_in_request(optional=optional, fresh=fresh, refresh=refresh, locations=locations)
      user = get_current_user()
      if config.getboolean('logging', 'log_requests'):
        logger.info(f"[user:{user.username if user is not None else 'Anonymous'}] [client:{request.remote_addr}] [request:{request}]")
      if user is not None:
        return func(*args, **kwargs)
      elif optional:
        return func(*args, **kwargs)

      return gs_make_response(status=GStatusCode.ERROR,
                              httpstatus=401)
    return jwtrequired
  return decorator

@jwt.additional_claims_loader
def add_claims_to_access_token(user: GSUser) -> dict:
  return {
    'id': user.id
  }

@jwt.user_identity_loader
def user_identity_lookup(user: GSUser) -> str:
  return user.id

@jwt.user_lookup_loader
def user_loader(header: dict, identity: dict) -> GSUser:
  return authentication_service.fetch_user(identity['sub'])

@jwt.invalid_token_loader
def invalid_token_loader(identity: dict) -> Response:
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.token_verification_failed_loader
def token_verification_failed_loader(header: dict, identity: dict) -> Response:
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.token_in_blocklist_loader
def is_token_revoked(decoded_header: dict, decoded_token: dict) -> bool:
  try:
    jti = decoded_token['jti']
    token = gsdb.fetchone(""" SELECT jwt_revoked
                                FROM gs_jwt
                               WHERE jwt_jti = %s;""", (jti,))
    if token is not None:
      return token['jwt_revoked']
    return True
  except Exception as e:
    logger.exception(e)
    return True

@jwt.user_lookup_error_loader
def custom_user_loader_error(header: str, identity: str) -> Response:
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.expired_token_loader
def expired_token_callback(header: dict, expired_token: dict) -> Response:
  token_type = expired_token['type']
  return gs_make_response(message=f'The {token_type} token has expired',
                          status=GStatusCode.ERROR,
                          httpstatus=401)

@jwt.unauthorized_loader
def unauth_handler(reason: str) -> Response:
  try:
    body = request.get_data().decode('utf-8')
    msg = f'[http:401] [client:{request.remote_addr}] [request:{request.url}] [body:{body}] [reason: {reason}]'
    logger.error(msg)
  except Exception as e:
    logger.exception(e)
  return gs_make_response(status=GStatusCode.ERROR,
                          httpstatus=401)

@authentication.route('/auth/register', methods=['POST'])
def register() -> Response:
  try:
    if request.json:      
      username = request.json.get('username', None)
      password = request.json.get('password', None)
      first_name = request.json.get('first_name', None)
      last_name = request.json.get('last_name', None)
      is_subscribed = request.json.get('is_subscribed', True)
      address1 = request.json.get('address1', '')
      city = request.json.get('city', '')
      state = request.json.get('state', '')
      zip_code = request.json.get('zip_code', '')

      if username is not None and password is not None and first_name is not None and last_name is not None:
        gs_user = Table('gs_user')
        qry = Query.from_(
          gs_user
        ).select(
          '*',
        ).where(
          gs_user.username == username
        )

        users = gsdb.fetchall(str(qry))

        if users is not None and len(users) > 0:
          return gs_make_response(message='The account already exists',
                                  status=GStatusCode.ERROR,
                                  httpstatus=400)

        else:
          user = authentication_service.create_user(
            username.lower(),
            password,
            first_name,
            last_name,
            is_subscribed,
            address1,
            city,
            state,
            zip_code
          )

          if user is not None:
            user = authentication_service.validate_user(username.lower(), password)
            token = authentication_service.get_user_token(user)

            response = gs_make_response(message='The account was created successfully', 
                                    httpstatus=201)

            set_access_cookies(response, token['access_token'])
            set_refresh_cookies(response, token['refresh_token'])

            return response
          else:
            return gs_make_response(message='The account could not be created',
                                    status=GStatusCode.ERROR,
                                    httpstatus=500)
      else:
        return gs_make_response(message='Your request is missing data',
                        status=GStatusCode.ERROR,
                        httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(status=GStatusCode.ERROR,
                            httpstatus=500)

@authentication.route('/auth', methods=['POST'])
def login() -> Response:
  try:
    if request.json:
      username = request.json.get('username', None)
      password = request.json.get('password', None)

      user = authentication_service.validate_user(username.lower(), password)

      if user is None:
        return gs_make_response(message='Invalid username or password',
                                status=GStatusCode.ERROR,
                                httpstatus=401)

      token = authentication_service.get_user_token(user)
      
      response = gs_make_response(data=token,
                                  message='Authentication successful',
                                  status=GStatusCode.SUCCESS,
                                  httpstatus=200)

      set_access_cookies(response, token['access_token'])
      set_refresh_cookies(response, token['refresh_token'])
      return response

    else:
      return gs_make_response(status=GStatusCode.ERROR,
                              httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(status=GStatusCode.ERROR,
                            httpstatus=500)

@authentication.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh() -> Response:
  try:
    current_user = get_jwt_identity()
    jwt = get_jwt()
    user = authentication_service.fetch_user(current_user)
    access_token = create_access_token(identity=user)
    refresh_token = request.cookies.get('_grubstack_refresh_token') or request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_access_token = decode_token(access_token)
    decoded_refresh_token = decode_token(refresh_token)
    authentication_service.add_token_to_database(access_token, app.config['JWT_IDENTITY_CLAIM'], user.username)
    token = {
      'username': user.username,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'stripe_customer_id': user.stripe_customer_id,
      'access_token': access_token,
      'access_token_expiration': decoded_access_token['exp'],
      'access_token_expires_in': decoded_access_token['exp'] - time.time(),
      'access_token_jti': decoded_access_token['jti'],
      'refresh_token': refresh_token,
      'refresh_token_expiration': decoded_refresh_token['exp'],
      'refresh_token_expires_in': decoded_refresh_token['exp'] - time.time(),
      'refresh_token_jti': decoded_refresh_token['jti']
    }

    response = gs_make_response(message='Token refresh successful',
                                data=token,
                                status=GStatusCode.SUCCESS,
                                httpstatus=200)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to refresh token',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@authentication.route('/auth/whoami', methods=['GET'])
@jwt_required()
def whoami() -> Response:
  try:
    user = authentication_service.fetch_user(get_jwt_identity())
    jwt = get_jwt()
    access_token = request.cookies.get('_grubstack_access_token')
    refresh_token = request.cookies.get('_grubstack_refresh_token')
    decoded_access_token = decode_token(access_token)
    decoded_refresh_token = decode_token(refresh_token)
    user = {
      'username': user.username,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'stripe_customer_id': user.stripe_customer_id,
      'access_token': access_token,
      'access_token_expiration': decoded_access_token['exp'],
      'access_token_expires_in': decoded_access_token['exp'] - time.time(),
      'access_token_jti': decoded_access_token['jti'],
      'refresh_token': refresh_token,
      'refresh_token_expiration': decoded_refresh_token['exp'],
      'refresh_token_expires_in': decoded_refresh_token['exp'] - time.time(),
      'refresh_token_jti': decoded_refresh_token['jti']
    }
    return gs_make_response(data=user)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(data={},
                            httpstatus=500,
                            status=GStatusCode.ERROR)

@authentication.route('/auth/tokens', methods=['GET'])
@jwt_required()
def get_tokens() -> Response:
  try:
    user_identity = get_jwt_identity()
    tokens = authentication_service.get_tokens(user_identity)

    return gs_make_response(data=tokens)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(data=[],
                            httpstatus=500,
                            status=GStatusCode.ERROR)

@authentication.route('/auth/logout', methods=['POST'])
def logout():
    resp = jsonify({})
    unset_jwt_cookies(resp)
    return resp, 200

app.register_blueprint(authentication, url_prefix=config.get('general', 'urlprefix', fallback='/'))
