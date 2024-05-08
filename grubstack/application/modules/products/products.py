import logging, json, subprocess

from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import get_jwt_identity

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response, generate_hash
from grubstack.envelope import GStatusCode

from grubstack.application.modules.authentication.authentication import jwt_required
from grubstack.application.modules.authentication.authentication_service import AuthenticationService

from .products_service import ProductService
from .products_utilities import get_prefix, format_app

products = Blueprint('products', __name__)
logger = logging.getLogger('grubstack')

product_service = ProductService()
authentication_service = AuthenticationService()

@products.route('/products/apps', methods=['GET'])
@jwt_required()
def get_all():
  try:
    json_data = []
    tenant_id = authentication_service.get_tenant_id()
    
    if tenant_id is not None:
      apps = product_service.get_all(tenant_id)
      
      for app in apps:
        slug = product_service.get_slug(app['tenant_id'])
        status = "stopped"

        cmd = "helm status grubstack-" + get_prefix(app['product_id']) + "-" + slug + "| grep 'STATUS: ' | awk {'print $2'}"

        try:
          resp = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
          status = resp[0].decode('utf8').strip()
        except Exception:
          pass

        json_data.append(format_app(app, status))

    return gs_make_response(data=json_data,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve apps',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@products.route('/products/shared-apps', methods=['GET'])
@jwt_required()
def get_shared_apps():
  try:
    json_data = []
    user_id = get_jwt_identity()
    
    if user_id is not None:
      apps = product_service.get_shared_apps(user_id)
      
      for app in apps:
        slug = product_service.get_slug(app['tenant_id'])
        status = "stopped"

        cmd = "helm status grubstack-" + get_prefix(app['product_id']) + "-" + slug + "| grep 'STATUS: ' | awk {'print $2'}"

        try:
          resp = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
          result = resp[0].decode('utf8').strip()
          if result:
            status = result
        except Exception:
          pass
        
        json_data.append(format_app(app, status))

    return gs_make_response(data=json_data,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve shared apps',
                            status=GStatusCode.ERROR,
                            httpstatus=500)
                            
@products.route('/products/app/restart', methods=['POST'])
@jwt_required()
def restart_app():
  try:
    if request.json:
      data = json.loads(request.data)
      app_id = data['app_id'] or None
      tenant_id = None
      
      if 'tenant_id' in data:
        tenant_id = data['tenant_id']

      if tenant_id is None:
        tenant_id = authentication_service.get_tenant_id()

      tenant_slug = product_service.get_slug(tenant_id)
      if app_id:
        product_id = product_service.get_app_product_id(tenant_id, app_id)
        match product_id:
          case 1:
            product_service.uninstall_api(tenant_id)
            product_service.install_api(tenant_id)
          case 2:
            product_service.uninstall_core(tenant_id)
            product_service.install_core(tenant_id)
          case 3:
            product_service.uninstall_web(tenant_id)
            product_service.install_web(tenant_id)

        return gs_make_response(message='App restarted successfully',
                                status=GStatusCode.SUCCESS,
                                httpstatus=200)

      return gs_make_response(message='Invalid request syntax',
                        status=GStatusCode.ERROR,
                        httpstatus=400)
    else:
      return gs_make_response(message='Invalid request syntax',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to restart app',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@products.route('/products/app/init', methods=['POST'])
@jwt_required()
def init_all_apps():
  try:
    user_id = get_jwt_identity()

    has_initialized = product_service.has_initialized_apps(user_id)

    if has_initialized is True:
      return gs_make_response(message='You have already initialized your apps',
                        status=GStatusCode.ERROR,
                        httpstatus=409)
    else:
      tenant_id = authentication_service.get_tenant_id()
      
      if tenant_id:
        product_service.init_apps(tenant_id)
        return gs_make_response(message='GrubStack suite initialized',
                                status=GStatusCode.SUCCESS,
                                httpstatus=201)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to init apps',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(products, url_prefix=config.get('general', 'urlprefix', fallback='/'))
 