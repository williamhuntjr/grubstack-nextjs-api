import logging, requests, json

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response

from grubstack.envelope import GStatusCode

from grubstack.application.modules.authentication.authentication import jwt_required
from grubstack.application.modules.authentication.authentication_service import AuthenticationService

from .shared_access_service import SharedAccessService

shared_access = Blueprint('shared_access', __name__)
logger = logging.getLogger('grubstack')

shared_access_service = SharedAccessService()
authentication_service = AuthenticationService()

@shared_access.route('/shared-access', methods=['GET'])
@jwt_required()
def get_trusted_users():
  try:
    json_data = []
    tenant_id = authentication_service.get_tenant_id()

    json_data = shared_access_service.get_all(tenant_id)

    return gs_make_response(data=json_data,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve trusted users',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@shared_access.route('/shared-access/<string:user_id>', methods=['DELETE'])
@jwt_required()
def delete_trusted_user(user_id: str):  
  try:
    tenant_id = authentication_service.get_tenant_id()
    shared_access_service.delete(user_id, tenant_id)

    return gs_make_response(message='Trusted user deleted',
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve specified trusted user',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@shared_access.route('/shared-access', methods=['POST'])
@jwt_required()
def create_trusted_user():  
  try:
    tenant_id = authentication_service.get_tenant_id()
    if request.json:
      data = json.loads(request.data)

      username = data['username']
      permissions = data['permissions']

      user = shared_access_service.get_user(username)
      if user == None:
        return gs_make_response(message='The specified user does not exist',
                      status=GStatusCode.ERROR,
                      httpstatus=404)

      if user[0] == get_jwt_identity():
        return gs_make_response(message='You cannot add yourself as you are the owner',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

      trusted_user_exists = shared_access_service.get(tenant_id, user[0])
      if trusted_user_exists != None:
        return gs_make_response(message='That trusted user already exists',
                  status=GStatusCode.ERROR,
                  httpstatus=409)

      shared_access_service.create(tenant_id, user[0], permissions)
      return gs_make_response(message='Trusted user created',
                              status=GStatusCode.SUCCESS,
                              httpstatus=201)
  
    else:
      return gs_make_response(message='Invalid request syntax',
                            status=GStatusCode.ERROR,
                            httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create trusted user',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@shared_access.route('/shared-access', methods=['PUT'])
@jwt_required()
def update_trusted_user():  
  try:
    tenant_id = authentication_service.get_tenant_id()
    if request.json:
      data = json.loads(request.data)

      username = data['username']
      permissions = data['permissions']

      user = shared_access_service.get_user(username)
      if user == None:
        return gs_make_response(message='The specified user does not exist',
                      status=GStatusCode.ERROR,
                      httpstatus=400)
      if user[0] == get_jwt_identity():
        return gs_make_response(message='You cannot update your status as you are the owner',
                                status=GStatusCode.ERROR,
                                httpstatus=400)

      trusted_user_exists = shared_access_service.get(tenant_id, user[0])
      if trusted_user_exists != None:
        shared_access_service.update(tenant_id, user[0], permissions)
        return gs_make_response(message='The trusted user has been updated',
                                status=GStatusCode.SUCCESS,
                                httpstatus=200)

      return gs_make_response(message='That trusted user does not exist on this tenant',
                              status=GStatusCode.SUCCESS)
  
    else:
      return gs_make_response(message='Invalid request syntax',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to create trusted user',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@shared_access.route('/shared-access/permissions', methods=['GET'])
@jwt_required()
def get_permissions():
  try:
    json_data = shared_access_service.get_all_permissions()

    return gs_make_response(data=json_data,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve permissions',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(shared_access, url_prefix=config.get('general', 'urlprefix', fallback='/'))
