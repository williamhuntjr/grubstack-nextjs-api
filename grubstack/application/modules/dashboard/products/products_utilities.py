import subprocess

import boto3
from flask import Response

from pypika import Query, Table, Parameter

from grubstack import app, config, gsdb, coredb
  
def get_prefix(product_id: int):
  match product_id:
    case 1:
      return "api"
    case 2:
      return "core"
    case 3:
      return "web"
    case default:
      return "api"

def create_dns(record: str, address: str):
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

def install_api(tenant_id: str):
  row = coredb.fetchone("SELECT slug, access_token FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
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
    row = gsdb.fetchone("SELECT * FROM gs_tenant_app WHERE tenant_id = %s AND product_id = '1' AND app_url = %s", (tenant_id, api_url,))
    if row == None:
      table = Table('gs_tenant_app')

      qry = Query.into(table).columns(
        'tenant_id',
        'product_id',
        'app_url',
      ).insert(Parameter('%s'), 1, Parameter('%s'))

      gsdb.execute(str(qry), (tenant_id, api_url,))

    proxy_servers = config.get('proxy','servers', fallback='107.161.173.97')
    server_list = proxy_servers.split(";")
    for proxy_server in server_list:
      create_dns('api-' + slug + '.grubstack.app', proxy_server)

def uninstall_api(tenant_id: str):
  row = coredb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
  if row:
    slug = row[0]
    try:
      cmd = "helm uninstall grubstack-api-%s" % (slug)
      result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except:
      pass

def install_core(tenant_id: str):
  row = coredb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
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
    row = gsdb.fetchone("SELECT * FROM gs_tenant_app WHERE tenant_id = %s AND product_id = '2' AND app_url = %s", (tenant_id, core_url,))
    if row == None:
      table = Table('gs_tenant_app')

      qry = Query.into(table).columns(
        'tenant_id',
        'product_id',
        'app_url',
      ).insert(Parameter('%s'), 2, Parameter('%s'))

      gsdb.execute(str(qry), (tenant_id, core_url,))

    proxy_servers = config.get('proxy','servers', fallback='107.161.173.97')
    server_list = proxy_servers.split(";")
    for proxy_server in server_list:
      create_dns('core-' + slug + '.grubstack.app', proxy_server)

def uninstall_core(tenant_id: str):
  row = coredb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
  if row:
    slug = row[0]
    try:
      cmd = "helm uninstall grubstack-core-%s" % (slug)
      result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except:
      pass

def install_web(tenant_id: str):
  row = coredb.fetchone("SELECT slug, access_token FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
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
    row = gsdb.fetchone("SELECT * FROM gs_tenant_app WHERE tenant_id = %s AND product_id = '3' AND app_url = %s", (tenant_id, web_url,))
    if row == None:
      table = Table('gs_tenant_app')

      qry = Query.into(table).columns(
        'tenant_id',
        'product_id',
        'app_url',
      ).insert(Parameter('%s'), 3, Parameter('%s'))

      gsdb.execute(str(qry), (tenant_id, web_url,))

    proxy_servers = config.get('proxy','servers', fallback='107.161.173.97')
    server_list = proxy_servers.split(";")
    for proxy_server in server_list:
      create_dns('web-' + slug + '.grubstack.app', proxy_server)

def uninstall_web(tenant_id: str):
  row = coredb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
  if row:
    slug = row[0]
    try:
      cmd = "helm uninstall grubstack-web-%s" % (slug)
      result = subprocess.Popen(f"ssh grubstack@vps.williamhuntjr.com {cmd}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except:
      pass

def init_apps(tenant_id: str):
  install_api(tenant_id)
  install_core(tenant_id)
  install_web(tenant_id)

def get_slug(tenantId: str):
  row = coredb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenantId,))
  if row != None:
    return row[0]
  return None
