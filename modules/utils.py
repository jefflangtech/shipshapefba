import os
from urllib.parse import urlparse

class Utils:
  @staticmethod
  def is_remote_path(path):
    parsed = urlparse(path)
    return bool(parsed.netloc)

  @staticmethod
  def is_local_path(path):
    return os.path.exists(path)