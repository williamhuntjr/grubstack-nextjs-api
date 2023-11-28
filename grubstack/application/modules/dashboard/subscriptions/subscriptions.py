import logging, json

from flask import Blueprint, request

from grubstack import app, config, gsdb
from grubstack.authentication import requires_auth
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode

from .subscriptions_service import SubscriptionService
from .subscriptions_utilities import format_subscription

subcriptions = Blueprint('subscriptions', __name__)
logger = logging.getLogger('grubstack')

subscription_service = SubscriptionService()

@subcriptions.route('/subscriptions', methods=['GET'])
@requires_auth
def index():
  try:
    subscriptions = subscription_service.index()
    return gs_make_response(data=subscriptions)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve subscription. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subcriptions.route('/subscription', methods=['GET'])
@requires_auth
def find():
  try:
    name = request.args.get('name')

    if name is not None:
      subscription = subscription_service.find(name)
      if subscription is not None:
        return gs_make_response(data=format_subscription(subscription))

      else:
        return gs_make_response(message='Subscription not found.',
                        status=GStatusCode.ERROR,
                        httpstatus=404)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve subscription. Please try again later.',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

app.register_blueprint(subcriptions, url_prefix=config.get('general', 'urlprefix', fallback='/'))
