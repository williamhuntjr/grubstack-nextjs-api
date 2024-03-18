import stripe

from pypika import Query, Table, Tables, Order, functions, Parameter

from grubstack import app, config, gsdb

stripe.api_key = app.config['STRIPE_API_KEY']

class AccountService:
  def __init__(self):
    pass

  def get_account(self, user_id: str):
    gs_user = Table('gs_user')
    qry = Query.from_(
      gs_user
    ).select(
      gs_user.first_name,
      gs_user.last_name,
      gs_user.address1,
      gs_user.city,
      gs_user.state,
      gs_user.zip_code,
      gs_user.is_subscribed
    ).where(
      gs_user.user_id == user_id
    )
    
    row = gsdb.fetchone(str(qry))

    formatted_user = {
      'first_name': row[0],
      'last_name': row[1],
      'address1': row[2],
      'city': row[3],
      'state': row[4],
      'zip_code': row[5],
      'is_subscribed': row[6]
    }

    return formatted_user

  def update_account(
    self,
    user_id: str,
    first_name: str,
    last_name: str,
    address1: str,
    city: str,
    state: str,
    zip_code: str,
    is_subscribed: bool,
    stripe_customer_id: str
  ):
    gs_user = Table('gs_user')

    qry = Query.update(
      gs_user
    ).set(
      gs_user.first_name, Parameter('%s')
    ).set(
      gs_user.last_name, Parameter('%s')
    ).set(
      gs_user.address1, Parameter('%s')
    ).set(
      gs_user.city, Parameter('%s')
    ).set(
      gs_user.state, Parameter('%s')
    ).set(
      gs_user.zip_code, Parameter('%s')
    ).set(
      gs_user.is_subscribed, Parameter('%s')
    ).where(
      gs_user.user_id == user_id
    )

    gsdb.execute(
      str(qry),
      (
        first_name,
        last_name,
        address1,
        city,
        state,
        zip_code,
        is_subscribed,
      )
    )

    full_name = str(first_name) + ' ' + str(last_name)
    address = {
      'line1': address1,
      'city': city,
      'state': state,
      'postal_code': zip_code,
      'country': 'US'
    }
    stripe.Customer.modify(stripe_customer_id, name=full_name, address=address)