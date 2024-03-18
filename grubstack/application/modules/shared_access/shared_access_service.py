import requests

from pypika import Query, Table, Tables, Order, functions, Parameter

from grubstack import app, config, gsdb, coredb

from .shared_access_utilities import format_permission

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
      gs_permission.name
    ).where(
      gs_user_permission.tenant_id == tenant_id
    ).where(
      gs_user_permission.user_id == user_id
    )

    permissions_list = []
    permissions = gsdb.fetchall(str(qry))

    for permission in permissions:
      permissions_list.append(
        permission[0]
      )

    return permissions_list
  
  def delete(self, user_id: str, tenant_id: str):
    gs_user_tenant, gs_user_permission = Tables('gs_user_tenant', 'gs_user_permission')

    qry = Query.from_(
      gs_user_tenant
    ).delete().where(
      gs_user_tenant.user_id == user_id
    ).where(
      gs_user_tenant.tenant_id == tenant_id
    )
    gsdb.execute(str(qry))

    qry = Query.from_(
      gs_user_permission
    ).delete().where(
      gs_user_permission.user_id == user_id
    ).where(
      gs_user_permission.tenant_id == tenant_id
    )
    gsdb.execute(str(qry))

  def create(self, tenant_id: str, user_id: str, permissions: list):
    gs_user_tenant, gs_permission, gs_user_permission, gs_tenant_app, gs_user_shared_app = Tables(
      'gs_user_tenant',
      'gs_permission',
      'gs_user_permission',
      'gs_tenant_app',
      'gs_user_shared_app'
    )

    qry = Query.into(
      gs_user_tenant
    ).columns(
      gs_user_tenant.user_id,
      gs_user_tenant.tenant_id,
      gs_user_tenant.is_owner
    ).insert(
      user_id,
      tenant_id,
      'f'
    )
    gsdb.execute(str(qry))

    qry = Query.from_(
      gs_tenant_app
    ).select(
      gs_tenant_app.app_id
    ).where(
      gs_tenant_app.tenant_id == tenant_id
    ).where(
      gs_tenant_app.product_id == '2'
    )
    core_id = gsdb.fetchone(str(qry))

    if core_id: 
      qry = Query.into(
        gs_user_shared_app
      ).columns(
        gs_user_shared_app.app_id,
        gs_user_shared_app.user_id,
      ).insert(
        core_id[0],
        user_id
      )
      gsdb.execute(str(qry))

    qry = Query.from_(
      gs_permission
    ).select(
      gs_permission.permission_id,
      gs_permission.name
    ).where(
      gs_permission.name.isin(permissions)
    )
    permissions_list = gsdb.fetchall(str(qry))
    
    for permission in permissions_list:
      qry = Query.into(
        gs_user_permission
      ).columns(
        gs_user_permission.tenant_id,
        gs_user_permission.user_id,
        gs_user_permission.permission_id
      ).insert(
        tenant_id,
        user_id,
        permission[0]
      )
      gsdb.execute(str(qry))

  def update(self, tenant_id: str, user_id: str, permissions: list):
    gs_user_tenant, gs_permission, gs_user_permission = Tables('gs_user_tenant', 'gs_permission', 'gs_user_permission')

    qry = Query.from_(
      gs_user_permission
    ).delete().where(
      gs_user_permission.user_id == user_id
    ).where(
      gs_user_permission.tenant_id == tenant_id
    )
    gsdb.execute(str(qry))

    qry = Query.from_(
      gs_permission
    ).select(
      gs_permission.permission_id,
      gs_permission.name
    ).where(
      gs_permission.name.isin(permissions)
    )
    permissions_list = gsdb.fetchall(str(qry))
    
    for permission in permissions_list:
      qry = Query.into(
        gs_user_permission
      ).columns(
        gs_user_permission.tenant_id,
        gs_user_permission.user_id,
        gs_user_permission.permission_id
      ).insert(
        tenant_id,
        user_id,
        permission[0]
      )
      gsdb.execute(str(qry))

  def get_user(self, username: str):
    gs_user = Table('gs_user')
    qry = Query.from_(
      gs_user
    ).select(
      '*'
    ).where(
      gs_user.username == Parameter('%s')
    )

    user = gsdb.fetchone(str(qry), (username,))

    return user
  
  def get(self, tenant_id: str, user_id: str):
    gs_user_tenant = Table('gs_user_tenant')
    qry = Query.from_(
      gs_user_tenant
    ).select(
      '*'
    ).where(
      gs_user_tenant.tenant_id == tenant_id
    ).where(
      gs_user_tenant.user_id == user_id
    )
    trusted_user = gsdb.fetchone(str(qry))

    return trusted_user

  def get_all_permissions(self):
    gs_permission = Table('gs_permission')
    qry = Query.from_(
      gs_permission
    ).select(
      gs_permission.permission_id,
      gs_permission.name,
      gs_permission.description
    )
    permissions = gsdb.fetchall(str(qry))
    
    json_data = []
    for permission in permissions:
      json_data.append(format_permission(permission))

    return json_data