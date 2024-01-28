import logging, json, subprocess

from flask import Blueprint, request
from flask_cors import cross_origin

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response, generate_hash
from grubstack.authentication import AuthError, requires_auth, requires_scope, get_user_id, get_tenant_id, get_tenant_slug
from grubstack.envelope import GStatusCode

from .products_service import ProductService
from .products_utilities import get_prefix

products = Blueprint('product', __name__)
logger = logging.getLogger('grubstack')

product_service = ProductService()

@products.route('/products/apps', methods=['GET'])
@requires_auth
def get_all():
  try:
    json_data = []

    tenant_id = get_tenant_id()
    
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
        
        json_data.append({
          "app_id": app['app_id'],
          "app_url": app['app_url'],
          "tenant_id": app['tenant_id'],
          "product_id": app['product_id'],
          "is_front_end_app": app['is_front_end_app'],
          "product_name": app['name'],
          "product_description": app['description'],
          "status": status
        })

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve apps. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@products.route('/products/shared-apps', methods=['GET'])
@requires_auth
def get_shared_apps():
  try:
    json_data = []
    user_id = get_user_id()
    
    if user_id is not None:
      apps = product_service.get_shared_apps(user_id)
      
      for app in apps:
        slug = product_service.get_slug(app['tenant_id'])
        status = "stopped"

        cmd = "helm status grubstack-" + get_prefix(app['product_id']) + "-" + slug + "| grep 'STATUS: ' | awk {'print $2'}"

        try:
          resp = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
          status = resp[0].decode('utf8').strip()
        except Exception:
          pass
        
        json_data.append({
          "app_id": app['app_id'],
          "app_url": app['app_url'],
          "tenant_id": app['tenant_id'],
          "product_id": app['product_id'],
          "is_front_end_app": app['is_front_end_app'],
          "product_name": app['name'],
          "product_description": app['description'],
          "status": status
        })

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve shared apps. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)
                            
@products.route('/products/app/restart', methods=['POST'])
@requires_auth
def restart_app():
  try:
    if request.json:
      tenant_id = get_tenant_id()
      tenant_slug = product_service.get_slug(tenant_id)

      data = json.loads(request.data)
      app_id = data['app_id']

      if app_id:
        product_id = product_service.get_app_product_id(tenant_id, app_id)

        if product_id is not None:
          if product_id == 1:
            product_service.uninstall_api(tenant_id)
            product_service.install_api(tenant_id)

          if product_id == 2:
            product_service.uninstall_core(tenant_id)
            product_service.install_core(tenant_id)
        
          if product_id == 3:
            product_service.uninstall_web(tenant_id)
            product_service.install_web(tenant_id)

        return gs_make_response(message='App restarted successfully')

      return gs_make_response(message='Unable to restart app',
                        status=GStatusCode.ERROR,
                        httpstatus=500)
    else:
      return gs_make_response(message='Invalid data',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to restart app. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@products.route('/products/app/init', methods=['POST'])
@requires_auth
def init_all_apps():
  try:
    user_id = get_user_id()

    has_initialized = product_service.has_initialized_apps(user_id)

    if has_initialized is True:
      return gs_make_response(message='You have already initialized your apps',
                        status=GStatusCode.ERROR,
                        httpstatus=400)
    else:
      tenant_id = get_tenant_id()
      
      if tenant_id:
        product_service.init_apps(tenant_id)
        return gs_make_response(message='GrubStack initialized.')

    return gs_make_response(message='Unable to init apps',
                  status=GStatusCode.ERROR,
                  httpstatus=500)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to init apps. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(products, url_prefix=config.get('general', 'urlprefix', fallback='/'))
 