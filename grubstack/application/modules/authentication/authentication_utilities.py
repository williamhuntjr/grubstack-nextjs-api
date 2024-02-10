from datetime import datetime

def epoch_to_datetime(epoch: int) -> datetime:
  return datetime.fromtimestamp(epoch)
