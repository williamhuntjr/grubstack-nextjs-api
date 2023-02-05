import logging, subprocess, json, random
from flask import Response

from grubstack import config, gsdb
from grubstack.envelope import GResponse, GStatusCode

logger = logging.getLogger('grubstack')

def gs_make_response(*args, **kwargs):
  xr = GResponse(
    kwargs.get('data') or kwargs.get('fallback'),
    kwargs.get('message') or '',
    kwargs.get('status') or GStatusCode.SUCCESS,
    kwargs.get('totalrowcount') or '',
    kwargs.get('totalpages') or '',
  )

  r = Response(xr.tojson(), status=kwargs.get('httpstatus') or 200,
               headers=kwargs.get('headers'))
  r.headers['Content-Type'] = 'application/json'
  return r

import subprocess, json

def init_apps(tenant_id: str):
  row = gsdb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenant_id,))
  if row:
    slug = row[0]
    data = {
      "slug": slug,
      "secret_id": generate_hash(16),
      "tenant_id": tenant_id,
      "db_server": config.get('database', 'server'),
      "db_name": config.get('database', 'core_db'),
      "db_port": config.get('database', 'port'),
      "db_user": config.get('database', 'user'),
      "db_password": config.get('database', 'password'),
      "corp_db_server": config.get('corporate', 'server'),
      "corp_db_name": config.get('corporate', 'database'),
      "corp_db_port": config.get('corporate', 'port'),
      "corp_db_user": config.get('corporate', 'user'),
      "corp_db_password": config.get('corporate', 'password'),
      "mail_server": config.get('mail', 'server'),
      "mail_port": config.get('mail', 'port'),
      "mail_ssl": config.get('mail', 'ssl'),
      "mail_user": config.get('mail', 'user'),
      "mail_password": config.get('mail', 'password')
    }
    file_path = '/tmp/grubstack-' + slug + '.json'
    f = open(file_path, "w")
    f.write(json.dumps(data))
    f.close()

    cur = gsdb.execute("INSERT INTO gs_tenant_app VALUES (DEFAULT, %s, '1', %s)", (tenant_id, 'https://api.grubstack.app/' + slug,))

    cmd = '/usr/bin/jinja -d /tmp/grubstack-' + slug + '.json ' + '/etc/grubstack/system.template.j2 > ' + '/etc/grubstack/system/' + slug + '.conf'
    create_api_config = subprocess.call(cmd, shell=True)

    cmd = '/usr/bin/jinja -d /tmp/grubstack-' + slug + '.json ' + '/etc/grubstack/nginx.template.j2 > ' + '/etc/grubstack/nginx/' + slug + '.conf'
    create_nginx_config = subprocess.call(cmd, shell=True)

    cmd = 'sudo systemctl restart grubstack-core-api@' + slug
    restart_app = subprocess.call(cmd, shell=True)

    cmd = 'sudo systemctl reload nginx'
    reload_nginx = subprocess.call(cmd, shell=True)

def generate_hash(num: int = 12):
  string = []
  chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
  for k in range(1, num+1):
    string.append(random.choice(chars))
  string = "".join(string)
  return string

def get_slug(tenantId: str):
  row = gsdb.fetchone("SELECT slug FROM gs_tenant WHERE tenant_id = %s", (tenantId,))
  if row != None:
    return row[0]
  return None