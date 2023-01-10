import logging
import psycopg2
import psycopg2.extras
from flask import current_app

logger = logging.getLogger("grubstack")

class GrubDatabase(object):
  def __init__(self, config, server=None, database=None, port=None, user=None, password=None, ssl=None):
    self.config     = config
    self.server     = server   or config.get('database',    'server',   fallback='localhost')
    self.database   = database or config.get('database',    'database', fallback='grubstack')
    self.port       = port     or config.getint('database', 'port',     fallback=5432)
    self.user       = user     or config.get('database',    'user',     fallback='admin')
    self.password   = password or config.get('database',    'password', fallback='admin')
    self.ssl        = ssl      or config.get('database',    'ssl',      fallback='prefer')
    self.connection = self.connect()

  def connect(self):
    try:
      con = psycopg2.connect(host=self.server,
                             database=self.database,
                             user=self.user,
                             password=self.password,
                             port=self.port,
                             sslmode=self.ssl,
                             connect_timeout=15)
      con.autocommit = True

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      return con

  def reconnect(self):
    del self.connection
    self.connection = self.connect()

  def get_cursor(self):
    try:
      cur = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
      if cur is not None:
        return cur
      else:
        self.reconnect()
        return None

    except Exception as e:
      print(e)
      return None

  def test_connection(self):
    """Checks if the database connection is still open"""
    try:
      if not self.connection or self.connection.closed != 0:
        self.reconnect()
    except Exception as e:
      print(e)
      pass

  def fetchone(self, query, params=None):
    """Execute query against database using params dict()"""
    try:
      cur = self.get_cursor()
      if cur is not None:
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close()
        return row
      else:
        self.reconnect()
        return None

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      if cur is not None:
        cur.close()
        del cur

  def fetchall(self, query, params=None):
    """Execute query against database using params dict()"""
    try:
      cur = self.get_cursor()
      if cur is not None:
        cur.execute(query, params)
        return cur.fetchall()
      else:
        self.reconnect()
        return None

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      if cur is not None:
        cur.close()
        del cur

  def execute(self, query, params=None):
    """Execute query against database using params dict()"""
    try:
      cur = self.get_cursor()
      if cur is not None:
        return cur.execute(query, params)
      else:
        self.reconnect()
        return None

    except Exception as e:
      logger.exception(e)
      return None

    finally:
      if cur is not None:
        cur.close()
        del cur

