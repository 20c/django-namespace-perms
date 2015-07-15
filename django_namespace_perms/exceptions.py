class PermissionDenied(Exception):
  def __init__(self, reason):
    super(Exception, self).__init__("Permission denied: %s" % reason)
