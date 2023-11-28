from pypika import Query, Table, Order

from grubstack import app, gsdb
from .subscriptions_utilities import format_subscription

class SubscriptionService:
  def __init__(self):
    pass
  
  def index(self):
    table = Table('gs_subscription')
    qry = Query.from_('gs_subscription').select('*').orderby('name', order=Order.asc)

    subscriptions = gsdb.fetchall(str(qry))
    subscriptions_list = []

    for subscription in subscriptions:
      subscriptions_list.append(format_subscription(subscription))

    return subscriptions_list

  def find(self, name: str):
    table = Table('gs_subscription')
    qry = Query.from_('gs_subscription').select('*').where(table.name == name)

    subscription = gsdb.fetchone(str(qry))

    if subscription is not None:
      return subscription
    
    return None

