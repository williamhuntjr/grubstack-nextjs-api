import logging, json, subprocess

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, get_current_user

from grubstack import app, config, gsdb, coredb

from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode

from grubstack.application.modules.authentication.authentication import jwt_required

from .account_service import AccountService

account = Blueprint('account', __name__)
logger = logging.getLogger('grubstack')

account_service = AccountService()

@account.route('/account', methods=['GET'])
@jwt_required()
def get_account():
  try:
    json_data = {}

    user_id = get_jwt_identity()

    if user_id != None:
      user_info = account_service.get_account(user_id)
      return gs_make_response(data=user_info)

    return gs_make_response(message='Unable to find account',
                            status=GStatusCode.ERROR,
                            httpstatus=401)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve account',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@account.route('/account', methods=['PUT'])
@jwt_required()
def update_account():
  try:
    first_name = request.json.get('first_name', None)
    last_name = request.json.get('last_name', None)
    address1 = request.json.get('address1', '')
    city = request.json.get('city', '')
    state = request.json.get('state', '')
    zip_code = request.json.get('zip_code', '')
    is_subscribed = request.json.get('is_subscribed', True)

    user_id = get_jwt_identity()
    customer_info = get_current_user()
    
    if user_id != None:
      user_info = account_service.update_account(
        user_id,
        first_name,
        last_name,
        address1,
        city,
        state,
        zip_code,
        is_subscribed,
        customer_info.stripe_customer_id
      )
      return gs_make_response(data=user_info)

    return gs_make_response(message='Unable to find account',
                            status=GStatusCode.ERROR,
                            httpstatus=401)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to update account',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(account, url_prefix=config.get('general', 'urlprefix', fallback='/'))
