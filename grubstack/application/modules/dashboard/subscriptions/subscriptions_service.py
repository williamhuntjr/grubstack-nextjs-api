import stripe
from pypika import Query, Table, Order

from grubstack import app, gsdb

from .subscriptions_utilities import format_limits
from .subscriptions_constants import ALLOWED_PRODUCTS

stripe.api_key = app.config['STRIPE_API_KEY']

class SubscriptionService:
  def __init__(self):
    pass

  def index(self, stripe_customer_id: str):
    subscriptions = stripe.Subscription.list(customer=stripe_customer_id)
    return subscriptions['data']

  def get(self, subscription_id: str):
    subscription_info = stripe.Subscription.retrieve(subscription_id)
    return subscription_info

  def get_product(self, product_id: str):
    product_info = stripe.Product.retrieve(product_id)
    return product_info

  def get_products(self):
    products = stripe.Product.list()
    products_list = []

    for product in products:
      product_prices = stripe.Price.list(product=product['id'])
      for price in product_prices:
        if price['lookup_key'] in ALLOWED_PRODUCTS:
          json_data = {
            "id": price['id'],
            "name": price['lookup_key'] or '',
            "price": price['unit_amount'],
            "product": price['product']
          }
          products_list.append(json_data)
    return products_list

  def get_product_prices(self, product_id: str):
    product_prices = stripe.Price.list(product=product_id)
    return product_prices['data']

  def create_subscription(self, tenant_id: str, customer_id: str, price_id: str):
    return stripe.Subscription.create(
      customer=customer_id,
      items=[{
        'price': price_id,
      }],
      payment_behavior='default_incomplete',
      payment_settings={'save_default_payment_method': 'on_subscription'},
      expand=['latest_invoice.payment_intent', 'pending_setup_intent'],
      metadata={
        'tenant_id': tenant_id
      }
    )

  def cancel_subscription(self, subscription_id: str):
    return stripe.Subscription.cancel(subscription_id)

  def upcoming_payment(self, customer_id: str, subscription_id: str):
    return stripe.Invoice.upcoming(customer=customer_id, subscription=subscription_id)
  
  def get_account_limits(self, tenant_id: str):
    if tenant_id != None:
      table = Table('gs_tenant_feature')
      qry = Query.from_('gs_tenant_feature').select('franchise_count', 'store_count', 'financial_report_lvl', 'backup_frequency', 'tech_support_lvl', 'is_shareable').where(table.tenant_id == tenant_id)

      limits = gsdb.fetchone(str(qry))

      return format_limits(limits)
    else:
      return {}