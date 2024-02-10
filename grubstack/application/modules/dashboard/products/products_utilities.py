def get_prefix(product_id: int):
  match product_id:
    case 1:
      return "api"
    case 2:
      return "core"
    case 3:
      return "web"
    case default:
      return "api"

def format_app(app: dict, status: str):
  formatted_app = {
    "app_id": app['app_id'],
    "app_url": app['app_url'],
    "tenant_id": app['tenant_id'],
    "product_id": app['product_id'],
    "is_front_end_app": app['is_front_end_app'],
    "product_name": app['name'],
    "product_description": app['description'],
    "status": status
  }

  return formatted_app