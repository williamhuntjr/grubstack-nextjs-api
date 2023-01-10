from . import app
import logging
from grubstack import gsdb

class GrubStackLogHandler(logging.Handler):

  def __init__(self):
    logging.Handler.__init__(self)

  def emit(self, record):
    qry = """INSERT INTO gs_log(log_created, log_asctime, log_name, log_loglevel, log_loglevelname,
                                         log_message, log_module, log_funcname, log_lineno, log_exception,
                                         log_process, log_thread, log_threadname) 
                                 VALUES (%(asctime)s, %(created)s, %(name)s, %(levelno)s, %(levelname)s,
                                         %(message)s, %(module)s, %(funcName)s,  %(lineno)s,  %(exc_text)s,
                                         %(process)s, %(thread)s, %(threadName)s);"""

    if record.exc_info:
      record.exc_text = logging._defaultFormatter.formatException(record.exc_info)
      record.message = logging._defaultFormatter.formatException(record.exc_info)
    else:
      record.exc_text = ""

    params = record.__dict__
    msg = self.format(record)

    try:
      cur = gsdb.getcursor()
      cur.execute(qry, params)
      cur.close()
    except Exception as e:
      print(f'Error getting database cursor for logging! Message: {e}')