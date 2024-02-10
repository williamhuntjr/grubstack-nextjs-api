import time

import stripe

from pypika import Query, Table, Parameter
from pypika import functions as fn

from flask_jwt_extended import (
  create_access_token, 
  decode_token,
  create_refresh_token, 
  get_jwt_identity,
  get_jti, 
  get_current_user, 
  current_user,
  verify_jwt_in_request
)

from grubstack import app, gsdb, bcrypt, coredb
from grubstack.user import GSUser
from grubstack.utilities import generate_hash

from .authentication_utilities import epoch_to_datetime

stripe.api_key = app.config['STRIPE_API_KEY']

class AuthenticationService:
  def __init__(self):
    pass

  def create_user(
    self,
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    is_subscribed: bool,
    address1: str,
    city: str,
    state: str,
    zip_code: str
  ):
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    gs_user = Table('gs_user')

    try:
      qry = Query.into(gs_user).columns(
        'username',
        'password',
        'create_time',
        'first_name',
        'last_name',
        'is_subscribed',
        'address1',
        'city',
        'state',
        'zip_code'
      ).insert(
        Parameter('%s'),
        password_hash,
        'now()',
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s'),
        Parameter('%s')
      )

      gsdb.execute(str(qry), (username, first_name, last_name, is_subscribed, address1, city, state, zip_code))

      qry = Query.from_(
        gs_user
      ).select(
        '*',
      ).where(
        gs_user.username == username
      )

      row = gsdb.fetchone(str(qry))

      if row is not None:
        resp = stripe.Customer.create(
          name=str(first_name) + " " + str(last_name),
          email=str(username),
        )
        stripe_customer_id = resp['id']

        qry = Query.update(gs_user).set(
          gs_user.stripe_customer_id, stripe_customer_id
        ).where(gs_user.user_id == row[0])

        gsdb.execute(str(qry))

        qry = Query.from_(
          gs_user
        ).select(
          '*',
        ).where(
          gs_user.username == username
        )

        row = gsdb.fetchone(str(qry))

        return row

      return None

    except Exception as e:
      return None
      
  def validate_user(self, username: str, password: str):
    try:
      gs_user = Table('gs_user')
      
      qry = Query.from_(
        gs_user
      ).select(
        '*',
      ).where(
        gs_user.username == Parameter('%s')
      )

      user = gsdb.fetchone(str(qry), (username.lower(),))

      if user is None:
        return None

      else:
        user_id = user['user_id']

        if user['is_suspended'] == True:
          return None

        if bcrypt.check_password_hash(str(user['password']),str(password)) is True:
          return self.fetch_user(user_id)

        else:
          return None

    except Exception as e:
      return None

  def fetch_user(self, user_id: int):
    gs_user = Table('gs_user')
    
    qry = Query.from_(
      gs_user
    ).select(
      '*',
    ).where(
      gs_user.user_id == Parameter('%s')
    )

    user = gsdb.fetchone(str(qry), (user_id,))

    if user is None:
      return None

    username = user['username']
    first_name = user['first_name']
    last_name = user['last_name']
    stripe_customer_id = user['stripe_customer_id']
    address1 = user['address1']
    city = user['city']
    state = user['state']
    zip_code = user['zip_code']

    return GSUser(
      user_id,
      username,
      first_name,
      last_name,
      stripe_customer_id,
      address1,
      city,
      state,
      zip_code
    )

  def add_token_to_database(self, encoded_token: str, identity_claim: str, username: str) -> None:
    decoded_token = decode_token(encoded_token)
    jti = decoded_token['jti']
    token_type = decoded_token['type']
    user_identity = decoded_token[identity_claim]
    expires = epoch_to_datetime(decoded_token['exp'])
    revoked = False

    gs_jwt = Table('gs_jwt')

    qry = Query.into(gs_jwt).columns(
      'jwt_jti',
      'jwt_token_type',
      'jwt_token',
      'jwt_user_identity',
      'jwt_revoked',
      'jwt_expires',
      'jwt_username'
    ).insert(
      jti,
      token_type,
      encoded_token,
      user_identity,
      revoked,
      expires,
      username
    )

    gsdb.execute(str(qry))

  def get_user_token(self, user: GSUser) -> dict:
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    decoded_access_token = decode_token(access_token)
    decoded_refresh_token = decode_token(refresh_token)
    self.add_token_to_database(access_token, app.config['JWT_IDENTITY_CLAIM'], user.username)
    self.add_token_to_database(refresh_token, app.config['JWT_IDENTITY_CLAIM'], user.username)
    return {
      'id': user.id,
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
      'refresh_token_jti': decoded_refresh_token['jti'],
    }

  def invalidate_tokens(self, username: str) -> None:
    gs_jwt = Table('gs_jwt')
    
    qry = Query.from_(gs_jwt).delete().where(gs_jwt.jwt_username == username.lower())
    gsdb.execute(str(qry))

  def get_tokens(self, user_identity: str):
    gs_jwt = Table('gs_jwt')

    qry = Query.from_(
      gs_jwt
    ).select(
      '*',
    ).where(
      gs_jwt.jwt_user_identity == user_identity
    ).where(
      gs_jwt.jwt_expires > fn.Now()
    ).where(
      gs_jwt.jwt_revoked != 't'
    )

    tokens = gsdb.fetchall(str(qry)) or list()
    formatted_tokens = [{'jti': token['jwt_jti'], 'expiration': token['jwt_expires'], 'type': token['jwt_token_type']} for token in tokens]

    return formatted_tokens

  def get_tenant_id(self):
    current_user = get_current_user()
    if  current_user:
      table = Table('gs_user_tenant')
      qry = Query.from_(table).select('tenant_id').where(table.user_id == current_user.id).where(table.is_owner == 't')
      row = gsdb.fetchone(str(qry))

      if row:
        return row['tenant_id']
      else:
        slug = generate_hash()
        access_token = generate_hash()

        table = Table('gs_tenant')
        qry = Query.into(table).columns(
          'is_suspended',
          'is_active',
          'slug',
          'access_token'
        ).insert('f', 't', Parameter('%s'), Parameter('%s'))
        coredb.execute(str(qry), (slug, access_token,))

        qry = Query.from_(table).select('tenant_id').where(table.slug == slug)
        row = coredb.fetchone(str(qry))

        table = Table('gs_user_tenant')
        qry = Query.into(table).columns(
          'user_id',
          'tenant_id',
          'is_owner',
        ).insert(Parameter('%s'), Parameter('%s'), 't')
        
        gsdb.execute(str(qry), (current_user.id, row['tenant_id'],))

        return row['tenant_id']
    return None