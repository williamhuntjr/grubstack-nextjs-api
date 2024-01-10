from pypika import Query, Table, Order

from grubstack import gsdb

from .subscriptions_constants import ALLOWED_PRODUCTS

def format_subscription(data: dict, product_data: dict):
  subscription = {
    "id": data['id'],
    "name": product_data['name'],
    "product_id": data['plan']['product'],
    "start_date": data['start_date'],
    "status": data['status'],
    "quantity": data['quantity'],
    "cost": data['plan']['amount'] / 100,
    "currency": data['currency'],
    "current_period_end": data['current_period_end'],
    "current_period_start": data['current_period_start'],
    "billing": data['collection_method'],
    "cancel_at_period_end": data['cancel_at_period_end']
  }

  return subscription

def format_limits(limits_data: dict):
  limits = {
    "franchise_count": limits_data['franchise_count'],
    "store_count": limits_data['store_count'],
    "backup_frequency": limits_data['backup_frequency'],
    "tech_support_lvl": limits_data['tech_support_lvl'],
    "financial_report_lvl": limits_data['financial_report_lvl'],
    "is_shareable": limits_data['is_shareable']
  }

  return limits

def generate_account_limits(tenant_id: str, customer_id: str, subscription_service: dict):
  if tenant_id != None:
    subscriptions = subscription_service.index(customer_id)

    if len(subscriptions) > 0:
      franchise_count = 0
      store_count = 0
      financial_report_lvl = 0
      tech_support_lvl = 0
      is_shareable = False
      backup_frequency = 'N'

      for subscription in subscriptions:
        for item in subscription['items']['data']:
          if item['price']['lookup_key'] in ALLOWED_PRODUCTS:
            table = Table('gs_subscription')
            qry = Query.from_('gs_subscription').select('franchise_count', 'store_count', 'financial_report_lvl', 'backup_frequency', 'tech_support_lvl', 'is_shareable').where(table.name == item['price']['lookup_key'])

            limits = gsdb.fetchone(str(qry))
              
            franchise_count += limits['franchise_count']
            store_count += limits['store_count']
            
            if limits['franchise_count'] == -1:
              franchise_count = -1

            if limits['store_count'] == -1:
              store_count = -1

            if limits['financial_report_lvl'] > financial_report_lvl:
              financial_report_lvl = limits['financial_report_lvl']

            if limits['tech_support_lvl'] > tech_support_lvl:
              financial_report_lvl = limits['tech_support_lvl']

            if limits['is_shareable'] == True:
              is_shareable = True

            if limits['backup_frequency'] == 'D':
              backup_frequency = 'D'

            if limits['backup_frequency'] == 'M' and backup_frequency == 'N':
              backup_frequency = 'M'

      table = Table('gs_tenant_feature')
      qry = Query.update(table).set(table.franchise_count, franchise_count).set(table.store_count, store_count).set(table.financial_report_lvl, financial_report_lvl).set(table.tech_support_lvl, tech_support_lvl).set(table.is_shareable, is_shareable).set(table.backup_frequency, backup_frequency).where(table.tenant_id == tenant_id)

      return gsdb.execute(str(qry))