import logging, requests

from flask import Blueprint, request

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

@shared_access.route('/shared-access/trusted-users', methods=['GET'])
@jwt_required()
def get_trusted_users():
  try:
    json_data = []
    tenant_id = authentication_service.get_tenant_id()

    json_data = shared_access_service.get_all(tenant_id)

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve trusted users',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(shared_access, url_prefix=config.get('general', 'urlprefix', fallback='/'))
