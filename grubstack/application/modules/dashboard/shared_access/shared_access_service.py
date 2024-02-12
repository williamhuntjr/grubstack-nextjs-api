import requests

from pypika import Query, Table, Tables, Order, functions, Parameter

from grubstack import app, config, gsdb, coredb

class SharedAccessService:
  def __init__(self):
    pass
  
  def get_all(self, tenant_id: str):
    gs_user_tenant, gs_user = Tables('gs_user_tenant', 'gs_user')
    
    qry = Query.from_(
      gs_user_tenant
    ).left_join(
      gs_user
    ).on(
      gs_user_tenant.user_id == functions.Cast(gs_user.user_id, 'text')
    ).select(
      gs_user_tenant.user_id,
      gs_user.username
    ).where(
      gs_user_tenant.tenant_id == tenant_id
    ).where(
      gs_user_tenant.is_owner == 'f'
    )

    users = gsdb.fetchall(str(qry))

    json_data = []
    
    for user in users:
      permissions = self.get_permissions(tenant_id, user[0])
      json_data.append({
        'id': user[0],
        'username': user[1],
        'permissions': permissions
      })
    return json_data
  
  def get_permissions(self, tenant_id: str, user_id: str):
    gs_user_permission, gs_permission = Tables('gs_user_permission', 'gs_permission')
    qry = Query.from_(
      gs_user_permission
    ).inner_join(
      gs_permission
    ).on(
      gs_user_permission.permission_id == gs_permission.permission_id
    ).select(
      gs_permission.permission_id,
      gs_permission.name
    ).where(
      gs_user_permission.tenant_id == tenant_id
    ).where(
      gs_user_permission.user_id == user_id
    )

    permissions_list = []
    permissions = gsdb.fetchall(str(qry))

    for permission in permissions:
      permissions_list.append({
        'id': permission[0],
        'name': permission[1]
      })

    return permissions_list