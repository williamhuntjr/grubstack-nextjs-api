def format_permission(permission: dict):
  formatted_data = {
    'id': permission[0],
    'name': permission[1],
    'description': permission[2]
  }
  return formatted_data