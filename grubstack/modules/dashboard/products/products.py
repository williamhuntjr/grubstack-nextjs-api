import logging, json, subprocess

from flask import Blueprint, request
from flask_cors import cross_origin

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response, init_apps, generate_hash, get_slug
from grubstack.authentication import AuthError, requires_auth, requires_scope, get_user_id, get_tenant_id, get_tenant_slug
from grubstack.envelope import GStatusCode

product = Blueprint('product', __name__)
logger = logging.getLogger('grubstack')

@product.route('/product/apps', methods=['GET'])
@requires_auth
@requires_scope("read:products")
def get_all():
  try:
    json_data = []
    user_id = get_user_id()
    row = gsdb.fetchone("SELECT tenant_id FROM gs_user_tenant WHERE user_id = %s AND is_owner = 't'", (user_id,))
    if row:
      tenant_id = row[0]
      apps = gsdb.fetchall("SELECT app_id, app_url, c.tenant_id, c.product_id, p.is_front_end_app, p.product_name, p.product_description FROM gs_tenant_app c INNER JOIN gs_product p on p.product_id = c.product_id WHERE c.tenant_id = %s", (tenant_id,))
      
      for app in apps:
        status = "stopped"
        if app['product_id'] == 1:
          try:
            slug = get_slug(app['tenant_id'])
            if slug:
              cmd = 'sudo systemctl is-active grubstack-core-api@' + slug
              check_status = subprocess.check_output(cmd, shell=True)
              status = check_status.decode('utf8', errors='strict').strip()

          except Exception:
            pass

        json_data.append({
          "app_id":app['app_id'],
          "app_url":app['app_url'],
          "tenant_id":app['tenant_id'],
          "product_id":app['product_id'],
          "is_front_end_app":app['is_front_end_app'],
          "product_name":app['product_name'],
          "product_description":app['product_description'],
          "status": status
        })

    return gs_make_response(data=json_data)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve products. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@product.route('/product/app/restart', methods=['POST'])
@requires_auth
@requires_scope("edit:products")
def restart_app():
  try:
    if request.json:
      data = json.loads(request.data)
      params = data['params']
      app_id = params['app_id']
      tenant_id = get_tenant_id()
      tenant_slug = get_slug(tenant_id)
      if app_id:
        row = gsdb.fetchone("SELECT product_id FROM gs_tenant_app WHERE tenant_id = %s AND app_id = %s", (tenant_id, app_id,))
        if row and 'product_id' in row and row['product_id'] == 1:
          cmd = 'sudo systemctl restart grubstack-core-api@' + tenant_slug
          restart_app = subprocess.call(cmd, shell=True)
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

@product.route('/product/app/init', methods=['POST'])
@requires_auth
@requires_scope("edit:products")
def init_all_apps():
  try:
    user_id = get_user_id()
    row = gsdb.fetchone("SELECT user_id, tenant_id, is_owner FROM gs_user_tenant WHERE is_owner = 't' AND user_id = %s", (user_id,))
    if row != None:
      return gs_make_response(message='You have already initialized your apps',
                        status=GStatusCode.ERROR,
                        httpstatus=409)
    else:
      # TODO: add check for existing slug
      slug = generate_hash(12)
      cur = gsdb.execute("INSERT INTO gs_tenant VALUES (DEFAULT, 'f', 't', %s)", (slug,))
      row = gsdb.fetchone("SELECT tenant_id FROM gs_tenant WHERE slug = %s", (slug,))
      if row:
        cur = gsdb.execute("INSERT INTO gs_user_tenant VALUES (%s, %s, 't')", (user_id, row[0],))
        init_apps(row[0])
        return gs_make_response(message='GrubStack initialized.')

    return gs_make_response(message='Unable to init apps',
                  status=GStatusCode.ERROR,
                  httpstatus=500)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to init apps. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(product, url_prefix=config.get('general', 'urlprefix', fallback='/'))
 