class PermissionDenied(Exception):

    def __init__(self, reason):
        super(PermissionDenied, self).__init__("Permission denied: %s" % reason)
