import boto3, subprocess

from pypika import Query, Table, Tables, Order, functions, Parameter

from grubstack import app, config, gsdb, coredb

class ProductService:
  def __init__(self):
    pass

  def get_all(self, tenant_id: str):
    gs_tenant_app, gs_product = Tables('gs_tenant_app', 'gs_product')
    qry = Query.from_(
      gs_tenant_app
    ).inner_join(
      gs_product
    ).on(
      gs_product.product_id == gs_tenant_app.product_id
    ).select(
      gs_tenant_app.app_id,
      gs_tenant_app.app_url,
      gs_tenant_app.tenant_id,
      gs_tenant_app.product_id,
      gs_product.name,
      gs_product.description,
      gs_product.is_front_end_app
    ).where(
      gs_tenant_app.tenant_id == tenant_id
    ).orderby(
      gs_product.name, order=Order.asc
    )

    apps = gsdb.fetchall(str(qry))
    return apps

  def get_shared_apps(self, user_id: str):
    gs_user_shared_app, gs_tenant_app, gs_product = Tables('gs_user_shared_app', 'gs_tenant_app', 'gs_product')
    qry = Query.from_(
      gs_user_shared_app
    ).inner_join(
      gs_tenant_app
    ).on(
      gs_tenant_app.app_id == gs_user_shared_app.app_id
    ).inner_join(
      gs_product
    ).on(
      gs_product.product_id == gs_tenant_app.product_id
    ).select(
      gs_user_shared_app.app_id,
      gs_tenant_app.app_url,
      gs_tenant_app.tenant_id,
      gs_tenant_app.product_id,
      gs_product.name,
      gs_product.description,
      gs_product.is_front_end_app
    ).where(
      gs_user_shared_app.user_id == user_id
    ).orderby(
      gs_product.name, order=Order.asc
    )
    apps = gsdb.fetchall(str(qry))

    return apps

  def get_app_product_id(self, tenant_id: str, app_id: int):
    gs_tenant_app = Table('gs_tenant_app')
    qry = Query.from_(
      gs_tenant_app
    ).select(
      gs_tenant_app.product_id
    ).where(
      gs_tenant_app.tenant_id == tenant_id
    ).where(
      gs_tenant_app.app_id == app_id
    )

    row = gsdb.fetchone(str(qry))

    if row is not None:
      product_id = row[0]
    else:
      product_id = None

    return product_id
  
  def has_initialized_apps(self, user_id: str):
    gs_user_tenant = Table('gs_user_tenant')
    qry = Query.from_(
      gs_user_tenant
    ).select(
      gs_user_tenant.tenant_id
    ).where(
      gs_user_tenant.is_owner == 't'
    ).where(
      gs_user_tenant.user_id == user_id
    )

    row = gsdb.fetchone(str(qry))

    if row is not None:
      gs_tenant_app = Table('gs_tenant_app')
      qry = Query.from_(
        gs_tenant_app
      ).select(
        '*'
      ).where(
        gs_tenant_app.tenant_id == row[0]
      )

      rows = gsdb.fetchall(str(qry))

      if len(rows) > 0:
        return True

    return False

  def get_slug(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug
    ).where(
      gs_tenant.tenant_id == tenant_id
    )

    row = coredb.fetchone(str(qry))

    if row != None:
      return row[0]

    return None

  def create_dns(self, record: str, address: str):
    client = boto3.client('route53', aws_access_key_id=config.get('aws','aws_access_key_id', fallback=''), aws_secret_access_key=config.get('aws', 'aws_secret_access_key', fallback=''))
    create_dns = { 
      "Changes": [ 
        {
          "Action": "UPSERT", 
          "ResourceRecordSet":  {  
            "Name": record, 
            "Type": "A", 
            "TTL": 3600, 
            "ResourceRecords":  [ 
              {
                "Value": address
              } 
            ] 
          }  
        }  
      ] 
    }

    response = client.change_resource_record_sets(
      HostedZoneId=config.get('aws','hostedzone_id', fallback=''),
      ChangeBatch=create_dns
    )

  def install_api(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug,
      gs_tenant.access_token
    ).where(
      gs_tenant.tenant_id == tenant_id
    )

    row = coredb.fetchone(str(qry))

    if row:
      slug = row[0]
      access_token = row[1]

      app_config = {
        "db_server": config.get('database', 'external_ip'),
        "db_name": config.get('database', 'core_db'),
        "db_port": config.get('database', 'port'),
        "db_user": config.get('database', 'user'),
        "db_password": config.get('database', 'password'),
        "db_ssl": config.get('database', 'ssl'),
        "corporate_db": config.get('database', 'database'),
        "mail_server": config.get('mail', 'server'),
        "mail_port": config.get('mail', 'port'),
        "mail_ssl": config.get('mail', 'ssl'),
        "mail_user": config.get('mail', 'user'),
        "mail_password": config.get('mail', 'password'),
        "auth0_domain": app.config['AUTH0_DOMAIN'],
        "auth0_audience": app.config['AUTH0_AUDIENCE'],
      }
      cmd = """helm install grubstack-api-%s --set customer.host=api-%s.grubstack.app \\
                                            --set customer.tenantId=%s \\
                                            --set customer.accessToken=%s \\
                                            --set database.host=%s \\
                                            --set database.name=%s \\
                                            --set database.port=%s \\
                                            --set database.ssl=%s \\
                                            --set database.user=%s \\
                                            --set database.password=%s \\
                                            --set database.corporate=%s \\
                                            --set auth0.domain=%s \\
                                            --set auth0.audience=%s \\
                                            /home/grubstack/grubstack-helm/grubstack-api""" % (slug, slug, tenant_id, access_token, app_config['db_server'], app_config['db_name'], app_config['db_port'], app_config['db_ssl'], app_config['db_user'], app_config['db_password'], app_config['corporate_db'], app_config['auth0_domain'], app_config['auth0_audience'])
      result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      api_url = 'https://api-' + slug + '.grubstack.app'

      gs_tenant_app = Table('gs_tenant_app')
      qry = Query.from_(
        gs_tenant_app
      ).select(
        '*'
      ).where(
        gs_tenant_app.tenant_id == tenant_id
      ).where(
        gs_tenant_app.product_id == '1'
      ).where(
        gs_tenant_app.app_url == api_url
      )

      row = gsdb.fetchone(str(qry))

      if row == None:
        qry = Query.into(
          gs_tenant_app
        ).columns(
          gs_tenant_app.tenant_id,
          gs_tenant_app.product_id,
          gs_tenant_app.app_url
        ).insert(
          Parameter('%s'),
          1,
          Parameter('%s')
        )

        gsdb.execute(str(qry), (tenant_id, api_url,))

      proxy_servers = config.get('proxy','servers', fallback='107.161.173.97')
      server_list = proxy_servers.split(";")

      for proxy_server in server_list:
        self.create_dns('api-' + slug + '.grubstack.app', proxy_server)

  def uninstall_api(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug
    ).where(
      gs_tenant.tenant_id == tenant_id
    )

    row = coredb.fetchone(str(qry))

    if row:
      slug = row[0]
      try:
        cmd = "helm uninstall grubstack-api-%s" % (slug)
        result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      except:
        pass

  def install_core(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug
    ).where(
      gs_tenant.tenant_id == tenant_id
    )

    row = coredb.fetchone(str(qry))

    if row:
      slug = row[0]
      app_config = {
        "api_url": "https://api-" + slug + ".grubstack.app",
        "production_url": "https://grubstack.app",
        "site_url": "https://core-" + slug + ".grubstack.app",
        "host": "core-" + slug + ".grubstack.app",
        "auth0_domain": app.config['AUTH0_DOMAIN'],
        "auth0_clientId": app.config['AUTH0_CLIENT_ID'],
      }

      cmd = """helm install grubstack-core-%s --set customer.host=%s \\
                                              --set customer.apiUrl=%s \\
                                              --set customer.productionUrl=%s \\
                                              --set customer.tenantId=%s \\
                                              --set customer.slug=%s \\
                                              --set customer.siteUrl=%s \\
                                              --set auth0.domain=%s \\
                                              --set auth0.clientId=%s \\
                                              /home/grubstack/grubstack-helm/grubstack-core""" % (slug, app_config['host'], app_config['api_url'], app_config['production_url'], tenant_id, slug, app_config['site_url'], app_config['auth0_domain'], app_config['auth0_clientId'])
      result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      core_url = 'https://core-' + slug + '.grubstack.app'
      
      gs_tenant_app = Table('gs_tenant_app')
      qry = Query.from_(
        gs_tenant_app
      ).select(
        '*'
      ).where(
        gs_tenant_app.tenant_id == tenant_id
      ).where(
        gs_tenant_app.product_id == '2'
      ).where(
        gs_tenant_app.app_url == core_url
      )

      row = gsdb.fetchone(str(qry))

      if row == None:
        qry = Query.into(
          gs_tenant_app
        ).columns(
          gs_tenant_app.tenant_id,
          gs_tenant_app.product_id,
          gs_tenant_app.app_url,
        ).insert(
          Parameter('%s'),
          2,
          Parameter('%s')
        )

        gsdb.execute(str(qry), (tenant_id, core_url,))

      proxy_servers = config.get('proxy','servers', fallback='107.161.173.97')
      server_list = proxy_servers.split(";")
      for proxy_server in server_list:
        self.create_dns('core-' + slug + '.grubstack.app', proxy_server)

  def uninstall_core(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug
    ).where(
      gs_tenant.tenant_id == tenant_id
    )

    row = coredb.fetchone(str(qry))

    if row:
      slug = row[0]
      try:
        cmd = "helm uninstall grubstack-core-%s" % (slug)
        result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      except:
        pass

  def install_web(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug,
      gs_tenant.access_token
    ).where(
      gs_tenant.tenant_id == tenant_id
    )

    row = coredb.fetchone(str(qry))

    if row:
      slug = row[0]
      access_token = row[1]

      app_config = {
        "api_url": "https://api-" + slug + ".grubstack.app",
        "production_url": "https://grubstack.app",
        "site_url": "https://web-" + slug + ".grubstack.app",
        "host": "web-" + slug + ".grubstack.app",
        "auth0_domain": app.config['AUTH0_DOMAIN'],
        "auth0_clientId": app.config['AUTH0_CLIENT_ID'],
      }

      cmd = """helm install grubstack-web-%s --set customer.host=%s \\
                                              --set customer.apiUrl=%s \\
                                              --set customer.productionUrl=%s \\
                                              --set customer.tenantId=%s \\
                                              --set customer.slug=%s \\
                                              --set customer.siteUrl=%s \\
                                              --set customer.accessToken=%s \\
                                              --set auth0.domain=%s \\
                                              --set auth0.clientId=%s \\
                                              /home/grubstack/grubstack-helm/grubstack-web""" % (slug, app_config['host'], app_config['api_url'], app_config['production_url'], tenant_id, slug, app_config['site_url'], access_token, app_config['auth0_domain'], app_config['auth0_clientId'])

      result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      web_url = 'https://web-' + slug + '.grubstack.app'
      
      gs_tenant_app = Table('gs_tenant_app')
      qry = Query.from_(
        gs_tenant_app
      ).select(
        '*'
      ).where(
        gs_tenant_app.tenant_id == tenant_id
      ).where(
        gs_tenant_app.product_id == '3'
      ).where(
        gs_tenant_app.app_url == web_url
      )
      row = gsdb.fetchone(str(qry))
      
      if row == None:
        qry = Query.into(
          gs_tenant_app
        ).columns(
          gs_tenant_app.tenant_id,
          gs_tenant_app.product_id,
          gs_tenant_app.app_url,
        ).insert(
          Parameter('%s'),
          3,
          Parameter('%s')
        )

        gsdb.execute(str(qry), (tenant_id, web_url,))

      proxy_servers = config.get('proxy','servers', fallback='107.161.173.97')
      server_list = proxy_servers.split(";")
      for proxy_server in server_list:
        self.create_dns('web-' + slug + '.grubstack.app', proxy_server)

  def uninstall_web(self, tenant_id: str):
    gs_tenant = Table('gs_tenant')
    qry = Query.from_(
      gs_tenant
    ).select(
      gs_tenant.slug
    ).where(
      gs_tenant.tenant_id == tenant_id
    )
    
    row = coredb.fetchone(str(qry))

    if row:
      slug = row[0]
      try:
        cmd = "helm uninstall grubstack-web-%s" % (slug)
        result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      except:
        pass

  def init_apps(self, tenant_id: str):
    self.install_api(tenant_id)
    self.install_core(tenant_id)
    self.install_web(tenant_id)