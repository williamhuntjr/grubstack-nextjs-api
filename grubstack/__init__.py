#!/usr/bin/env python
__version__ = '0.1.0'
import logging, configparser, os, sys, argparse
from flask import Flask
from flask_mail import Mail
from flask_cors import CORS
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .database import GrubDatabase

config = configparser.RawConfigParser()
configfile = os.path.dirname(os.path.realpath(__file__)) + '/grubstack.ini'

if len(sys.argv) > 1:
  parser = argparse.ArgumentParser()
  parser.add_argument('-c', '--config', dest='config', help='full path to GrubStack API config file')
  args, extra = parser.parse_known_args()
  if args.config is not None:
    configfile = args.config
    print('INFO: Using config file from command line argument.')
    
elif os.environ.get('GRUBSTACK_CONFIG_FILE') is not None:
  configfile = os.environ.get('GRUBSTACK_CONFIG_FILE')
  print('INFO: Using config file from environment variable.')

tmpfile = Path(configfile)
if not tmpfile.exists():
  print('ERROR: Config file not found: {}'.format(configfile))
  sys.exit(-1)

print('INFO: Loading config from {}'.format(configfile))

config.read(configfile)
app = Flask(__name__, static_folder='../static')

# General settings
app.config['CONFIG_FILE']        = configfile
app.config['VERSION']            = __version__
app.config['DEBUG']              = config.getboolean('general', 'debug', fallback=False)
app.config['SECRET_KEY']         = config.get('general', 'secret')

# flask-limiter
app.config['RATELIMIT_ENABLED']         = config.getboolean('ratelimit', 'enabled', fallback=False)
app.config['RATELIMIT_DEFAULT']         = config.get('ratelimit', 'default_limit')
app.config['RATELIMIT_STRATEGY']        = config.get('ratelimit', 'strategy')
app.config['RATELIMIT_HEADERS_ENABLED'] = config.getboolean('ratelimit', 'headers_enabled')

# flask-mail
app.config['MAIL_ENABLED']        = config.getboolean('mail', 'enabled', fallback=False)
app.config['MAIL_SERVER']         = config.get('mail', 'server')
app.config['MAIL_PORT']           = config.getint('mail', 'port')
app.config['MAIL_USE_TLS']        = config.getboolean('mail', 'tls')
app.config['MAIL_USERNAME']       = config.get('mail', 'user')
app.config['MAIL_PASSWORD']       = config.get('mail', 'password')
app.config['MAIL_DEFAULT_SENDER'] = config.get('mail', 'from')
app.config['MAIL_DEBUG']          = config.getboolean('mail', 'debug', fallback=False)

# auth0
app.config['AUTH0_DOMAIN'] = 'dev-x2xvjtterdxi3zgj.us.auth0.com'
app.config['AUTH0_AUDIENCE'] = 'https://api.grubstack.app/v1'
app.config['AUTH0_CLIENT_ID'] = 'fzdrD4DJDsg992k2KCr3rngy9Ph6W5YG'

# Initialize globals
mail = Mail(app)
gsdb = GrubDatabase(config)
coredb = GrubDatabase(config, database='grubstack_core')
cors = CORS(app, supports_credentials=True)

# Logger
from .loghandler import GrubStackLogHandler
logformatter = logging.Formatter(config.get('logging', 'log_format', 
                                            fallback='[%(asctime)s] [%(name)s] [%(levelname)s] [%(module)s/%(funcName)s/%(lineno)d] %(message)s'))
logformatter.default_msec_format = config.get('logging', 'log_msec_format', fallback='%s.%03d')

logger = logging.getLogger()
logger.setLevel(config.getint('logging', 'log_min_level', fallback=20))

# Child logger visibility
logger.propagate = True

# Logging type
if config.getboolean('logging', 'log_to_file', fallback=True):
  filehandler = RotatingFileHandler(config.get('logging', 'log_to_file_name', fallback='grubstack.log'), maxBytes=(1048576*5), backupCount=7)
  filehandler.setFormatter(logformatter)
  logger.addHandler(filehandler)

if config.getboolean('logging', 'log_to_console', fallback=True):
  consolehandler = logging.StreamHandler()
  consolehandler.setFormatter(logformatter)
  logger.addHandler(consolehandler)

if config.getboolean('logging', 'log_to_database', fallback=False):
  gshandler = GrubStackLogHandler()
  gshandler.setFormatter(logformatter)
  logger.addHandler(gshandler)

from . import grubstack
from . import authentication
from . import application
