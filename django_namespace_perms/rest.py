from rest_framework import permissions
from django_namespace_perms.util import has_perms, obj_to_namespace
from django_namespace_perms.constants import PERM_READ, PERM_WRITE 
import logging

log = logging.getLogger(__name__)

class BasePermission(permissions.BasePermission):

  def debug(self, msg):
    log.debug(msg)
  
  def has_permission(self, request, view):
    log.debug("Check permission: %s, %s" % (request.method, view))
    if request.method == "POST":
      return has_perms(request.user, view.model, PERM_WRITE)
    else:
      return True

  def has_object_permission(self, request, view, obj):
    log.debug("Check Object permissions %s, %s, %s" % (
      request.method,
      request.user,
      obj_to_namespace(obj)
    ))

    if request.method in permissions.SAFE_METHODS:
      return has_perms(request.user, obj, PERM_READ)
    else:
      return has_perms(request.user, obj, PERM_WRITE)
