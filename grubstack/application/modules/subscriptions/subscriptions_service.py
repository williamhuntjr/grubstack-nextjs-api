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
            "name": product['name'],
            "nickname": price['nickname'],
            "lookup_key": price['lookup_key'] or '',
            "price": price['unit_amount'],
            "product": price['product'],
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
      gs_tenant_feature = Table('gs_tenant_feature')
      qry = Query.from_(
        gs_tenant_feature
      ).select(
        gs_tenant_feature.location_count,
        gs_tenant_feature.financial_report_lvl,
        gs_tenant_feature.backup_frequency,
        gs_tenant_feature.tech_support_lvl,
        gs_tenant_feature.is_shareable
      ).where(
        gs_tenant_feature.tenant_id == tenant_id
      )

      limits = gsdb.fetchone(str(qry))
      
      if limits:
        return format_limits(limits)
      else:
        return {}
    else:
      return {}

  def generate_account_limits(self, tenant_id: str, customer_id: str):
    if tenant_id != None:
      subscriptions = self.index(customer_id)

      if len(subscriptions) > 0:
        location_count = 0
        financial_report_lvl = 0
        tech_support_lvl = 0
        is_shareable = False
        backup_frequency = 'N'

        for subscription in subscriptions:
          for item in subscription['items']['data']:
            if item['price']['lookup_key'] in ALLOWED_PRODUCTS:
              gs_subscription = Table('gs_subscription')
              qry = Query.from_(
                gs_subscription
              ).select(
                gs_subscription.location_count,
                gs_subscription.financial_report_lvl,
                gs_subscription.backup_frequency,
                gs_subscription.tech_support_lvl,
                gs_subscription.is_shareable
              ).where(
                gs_subscription.name == item['price']['lookup_key']
              )

              limits = gsdb.fetchone(str(qry))

              if limits['location_count'] != -1 and location_count != -1:
                location_count += limits['location_count']

              if limits['location_count'] == -1:
                location_count = -1

              if limits['financial_report_lvl'] > financial_report_lvl:
                financial_report_lvl = limits['financial_report_lvl']

              if limits['tech_support_lvl'] > tech_support_lvl:
                tech_support_lvl = limits['tech_support_lvl']

              if limits['is_shareable'] == True:
                is_shareable = True

              if limits['backup_frequency'] == 'D':
                backup_frequency = 'D'

              if limits['backup_frequency'] == 'M' and backup_frequency == 'N':
                backup_frequency = 'M'

        gs_tenant_feature = Table('gs_tenant_feature')
        qry = Query.from_(
          gs_tenant_feature
        ).select(
          '*'
        ).where(
          gs_tenant_feature.tenant_id == tenant_id
        )

        row = gsdb.fetchone(str(qry))

        if row != None:
          qry = Query.update(gs_tenant_feature).set(
              gs_tenant_feature.location_count, location_count
            ).set(
              gs_tenant_feature.financial_report_lvl, financial_report_lvl
            ).set(
              gs_tenant_feature.tech_support_lvl, tech_support_lvl
            ).set(
              gs_tenant_feature.is_shareable, is_shareable
            ).set(
              gs_tenant_feature.backup_frequency, backup_frequency
            ).where(
              gs_tenant_feature.tenant_id == tenant_id
            )
        else:
          qry = Query.into(
            gs_tenant_feature
          ).insert(
            tenant_id,
            location_count,
            backup_frequency,
            is_shareable,
            tech_support_lvl,
            financial_report_lvl
          )
       
        gsdb.execute(str(qry))