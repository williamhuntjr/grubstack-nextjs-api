class GSUser(object):    
  def __init__(
    self,
    uid = None,
    username = str(),
    first_name = str(),
    last_name = str(),
    stripe_customer_id = str(),
    address1 = str(),
    city = str(),
    state = str(),
    zip_code = str(),
  ):
    self.id       = uid
    self.username = username
    self.first_name = first_name
    self.last_name = last_name
    self.stripe_customer_id = stripe_customer_id
    self.address1 = address1
    self.city = city
    self.state = state
    self.zip_code = zip_code
    self.reqsign  = None
    self.signkey  = None