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