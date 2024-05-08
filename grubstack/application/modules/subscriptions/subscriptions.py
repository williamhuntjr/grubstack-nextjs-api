import logging, json, stripe

from flask import Blueprint, request
from flask_jwt_extended import get_current_user

from grubstack import app, config, gsdb
from grubstack.utilities import gs_make_response
from grubstack.envelope import GStatusCode

from grubstack.application.modules.authentication.authentication import jwt_required
from grubstack.application.modules.authentication.authentication_service import AuthenticationService

from .subscriptions_service import SubscriptionService
from .subscriptions_utilities import format_subscription

webhook_secret = app.config['STRIPE_WEBHOOK']

subscriptions = Blueprint('subscriptions', __name__)
logger = logging.getLogger('grubstack')

subscription_service = SubscriptionService()
authentication_service = AuthenticationService()

@subscriptions.route('/subscriptions', methods=['GET'])
def index():
  try:
    products = subscription_service.get_products()
    return gs_make_response(data=products)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve products',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/account-limits', methods=['GET'])
@jwt_required()
def get_account_limits():
  try:
    tenant_id = authentication_service.get_tenant_id()
    limits = subscription_service.get_account_limits(tenant_id)
    return gs_make_response(data=limits,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve account limits',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/user/<string:subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id: str):
  try:
    subscription = subscription_service.get(subscription_id)
    return gs_make_response(data=subscription,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve subscription',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/upcoming-payment/<string:subscription_id>', methods=['GET'])
@jwt_required()
def get_upcoming_payment(subscription_id: str):
  try:
    user = get_current_user()
    payment = subscription_service.upcoming_payment(user.stripe_customer_id, subscription_id)

    return gs_make_response(data=payment,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve upcoming payment',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/product/<string:product_id>', methods=['GET'])
def get_product(product_id: str):
  try:
    product = subscription_service.get_product(product_id)
    return gs_make_response(data=product,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve product',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/product/<string:product_id>/prices', methods=['GET'])
def get_product_prices(product_id: str):
  try:
    product_prices = subscription_service.get_product_prices(product_id)
    return gs_make_response(data=product_prices)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve product prices',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/user', methods=['GET'])
@jwt_required()
def user_subscriptions_index():
  try:
    json_data = []

    user = get_current_user()
    if user.stripe_customer_id != None:
      subscriptions = subscription_service.index(user.stripe_customer_id)

      for subscription in subscriptions:
        json_data.append(format_subscription(subscription, subscription_service.get_product(subscription['plan']['product'])))

    return gs_make_response(data=json_data,
                            status=GStatusCode.SUCCESS,
                            httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Unable to retrieve user subscription',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions', methods=['POST'])
@jwt_required()
def create_subscription():
  try:
    if request.json:
      json_data = {}
      tenant_id = authentication_service.get_tenant_id()
      
      data = json.loads(request.data)

      customer_id = data['customer_id']
      price_id = data['price_id']
      
      subscription = subscription_service.create_subscription(tenant_id, customer_id, price_id)

      if subscription.pending_setup_intent is not None:
        json_data = {
          'type': 'setup',
          'cientSecret': subscription.pending_setup_intent.client_secret
        }
      else:
        json_data = {
          'type': 'payment',
          'clientSecret': subscription.latest_invoice.payment_intent.client_secret
        }

      return gs_make_response(data=json_data,
                              status=GStatusCode.SUCCESS,
                              httpstatus=201)

    else:
      return gs_make_response(message='Invalid request syntax',
                              status=GStatusCode.ERROR,
                              httpstatus=400)

  except Exception as e:
    logger.exception(e.user_message)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/<string:subscription_id>', methods=['DELETE'])
@jwt_required()
def delete_subscription(subscription_id: str):
  try:
    user = get_current_user()

    subscription = subscription_service.get(subscription_id)
    if subscription['customer'] != user.stripe_customer_id:
      return gs_make_response(message='Forbidden',
                        status=GStatusCode.ERROR,
                        httpstatus=403)
    else:
      subscription_service.cancel_subscription(subscription_id)
      return gs_make_response(message='Subscription deleted',
                              status=GStatusCode.SUCCESS,
                              httpstatus=200)

  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscriptions/<string:subscription_id>', methods=['PUT'])
@jwt_required()
def update_subscription(subscription_id: str):
  try:
    if request.json:
      data = json.loads(request.data)

      if 'cancel_at_period_end' in data:
        stripe.Subscription.modify(subscription_id, cancel_at_period_end=data['cancel_at_period_end'])

      return gs_make_response(message='Subscription updated successfully',
                              status=GStatusCode.SUCCESS,
                              httpstatus=200)
    else:
      return gs_make_response(message='Invalid request syntax',
                        status=GStatusCode.ERROR,
                        httpstatus=400)
  except Exception as e:
    logger.exception(e)
    return gs_make_response(message='Error processing request',
                            status=GStatusCode.ERROR,
                            httpstatus=500)

@subscriptions.route('/subscription-webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'customer.subscription.created':
      subscription = event['data']['object']
      subscription_service.generate_account_limits(subscription['metadata']['tenant_id'], subscription['customer'])
    elif event['type'] == 'customer.subscription.deleted':
      subscription = event['data']['object']
      subscription_service.generate_account_limits(subscription['metadata']['tenant_id'], subscription['customer'])
    elif event['type'] == 'customer.subscription.paused':
      subscription = event['data']['object']
    elif event['type'] == 'customer.subscription.pending_update_applied':
      subscription = event['data']['object']
    elif event['type'] == 'customer.subscription.pending_update_expired':
      subscription = event['data']['object']
    elif event['type'] == 'customer.subscription.resumed':
      subscription = event['data']['object']
    elif event['type'] == 'customer.subscription.trial_will_end':
      subscription = event['data']['object']
    elif event['type'] == 'customer.subscription.updated':
      subscription = event['data']['object']
      subscription_service.generate_account_limits(subscription['metadata']['tenant_id'], subscription['customer'])
    elif event['type'] == 'subscription_schedule.aborted':
      subscription_schedule = event['data']['object']
    elif event['type'] == 'subscription_schedule.canceled':
      subscription_schedule = event['data']['object']
    elif event['type'] == 'subscription_schedule.completed':
      subscription_schedule = event['data']['object']
    elif event['type'] == 'subscription_schedule.created':
      subscription_schedule = event['data']['object']
    elif event['type'] == 'subscription_schedule.expiring':
      subscription_schedule = event['data']['object']
    elif event['type'] == 'subscription_schedule.released':
      subscription_schedule = event['data']['object']
    elif event['type'] == 'subscription_schedule.updated':
      subscription_schedule = event['data']['object']
    # ... handle other event types
    else:
      print('Unhandled event type {}'.format(event['type']))

    return gs_make_response(status=GStatusCode.SUCCESS,
                            httpstatus=200)

app.register_blueprint(subscriptions, url_prefix=config.get('general', 'urlprefix', fallback='/'))
