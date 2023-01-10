import logging
from datetime import datetime
from flask import Blueprint, Response, g, jsonify
from . import app, gsdb
from .authentication import AuthError

gsapi = Blueprint('gsapi', __name__)
logger = logging.getLogger('grubstack')

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

@app.before_request
def before_request() -> None:
  '''Runs before every request in Flask'''
  g.start = datetime.now().timestamp()

@app.after_request
def after_request(response: Response) -> Response:
  response.headers['Server'] = 'GrubStack'
  response.headers['Strict-Transport-Security'] = 'max-age=2592000' # 30 days in seconds

  if 'Cache-Control' not in response.headers:
    response.headers['Cache-Control'] = 'no-store'

  return response

try:
  from uwsgidecorators import postfork
  @postfork
  def reconnectafterfork():
    '''
    This function handles uwsgi's postfork signal and forces a reconnection to the database. This is required
    when uwsgi is run without lazy-apps because uwsgi forks after loading the app, and since psycopg2 is not
    green-thread safe database queries will fail unless each thread establishes its own connection after the fork.
    '''
    gsdb.reconnect()
except ImportError:
  pass

app.register_blueprint(gsapi)
