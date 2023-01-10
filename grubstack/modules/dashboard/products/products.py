import logging

from flask import Blueprint
from flask_cors import cross_origin

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.authentication import AuthError, requires_auth, requires_scope, get_user_id
from grubstack.envelope import GStatusCode

product = Blueprint('product', __name__)
logger = logging.getLogger('grubstack')

@product.route('/products', methods=['GET'])
@requires_auth
def get_all():
  if requires_scope("read:products"):
    try:
      json_data = []
      user_id = get_user_id()
      resp = gsdb.fetchall("SELECT c.product_id, product_name, product_description, p.tenant_id, p.app_url FROM gs_product c INNER JOIN gs_user_product p ON p.product_id = c.product_id WHERE p.user_id = %s;", (user_id,))
      for product in resp:
        json_data.append({
          "product_id": product['product_id'],
          "product_name": product['product_name'],
          "product_description": product['product_description'],
          "tenant_id": product['tenant_id'],
          "app_url": product['app_url'],
        })
      return gs_make_response(data=json_data)

    except Exception as e:
      logger.exception(e)
      return gs_make_response(message='Unable to retrieve products. Please try again later.',
                              status=GStatusCode.ERROR,
                              httpstatus=500)

  raise AuthError({
    "code": "Unauthorized",
    "description": "You don't have access to this resource"
  }, 403)

app.register_blueprint(product, url_prefix=config.get('general', 'urlprefix', fallback='/'))
