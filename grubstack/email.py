from threading import Thread
from grubstack import mail, app, config
from flask_mail import Message
import smtplib, logging

logger = logging.getLogger("grubstack")

def send_async_email(app, msg):
  with app.app_context():
    mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
  if config.getboolean('mail', 'enabled'):
    try:
      msg = Message(subject, sender=sender, recipients=recipients)
      msg.html = html_body
      Thread(target=send_async_email, args=(app, msg)).start()
    except smtplib.SMTPRecipientsRefused:
      logger.error("Could not send email to " + recipients)
    except smtplib.SMTPAuthenticationError:
      logger.error("Authentication error when sending email")
    except Exception as e:
      logger.error(e)
