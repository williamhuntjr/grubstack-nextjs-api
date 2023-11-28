from pypika import Query, Table, Order, functions

from grubstack import app, gsdb

class ProductService:
  def __init__(self):
    pass

  def get_all(self, tenant_id: str):
    apps = gsdb.fetchall("SELECT app_id, app_url, c.tenant_id, c.product_id, p.is_front_end_app, p.name, p.description FROM gs_tenant_app c INNER JOIN gs_product p on p.product_id = c.product_id WHERE c.tenant_id = %s ORDER BY name ASC", (tenant_id,))
    
    return apps

  def get_tenant_id(self, user_id: str):
    table = Table('gs_user_tenant')
    qry = Query.from_('gs_user_tenant').select('tenant_id').where(table.user_id == user_id).where(table.is_owner == 't')

    tenant = gsdb.fetchone(str(qry))

    if tenant is not None:
      return tenant[0]
    else:
      return None

  def get_app_product_id(self, tenant_id: str, app_id: int):
    table = Table('gs_tenant_app')
    qry = Query.from_('gs_tenant_app').select('product_id').where(table.tenant_id == tenant_id).where(table.app_id == app_id)

    app = gsdb.fetchone(str(qry))

    if app is not None:
      product_id = app[0]
    else:
      product_id = None

    return product_id
  
  def has_initialized_apps(user_id: str):
    table = Table('gs_user_tenant')
    qry = Query.from_('gs_user_tenant').select('*').where(table.is_owner == 't').where(table.user_id == user_id)

    resp = gsdb.fetchone(str(qry))

    if resp is not None:
      return True

    return False