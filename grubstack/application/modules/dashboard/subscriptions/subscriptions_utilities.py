def format_subscription(data: dict):
  subscription = {
    "id": data['subscription_id'],
    "name": data['name'],
    "price": data['price']
  }

  return subscription