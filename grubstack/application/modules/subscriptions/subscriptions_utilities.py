def format_subscription(data: dict, product_data: dict):
  subscription = {
    "id": data['id'],
    "name": product_data['name'],
    "nickname": data['plan']['nickname'],
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
    "location_count": limits_data['location_count'],
    "backup_frequency": limits_data['backup_frequency'],
    "tech_support_lvl": limits_data['tech_support_lvl'],
    "financial_report_lvl": limits_data['financial_report_lvl'],
    "is_shareable": limits_data['is_shareable']
  }

  return limits
