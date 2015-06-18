from rest_framework import permissions, serializers

from django_namespace_perms.util import (
  has_perms, 
  obj_to_namespace,
  permissions_apply_to_serialized_model
)

from django_namespace_perms.constants import PERM_READ, PERM_WRITE 
import logging


log = logging.getLogger(__name__)

class BasePermission(permissions.BasePermission):

  def debug(self, msg):
    print msg
    log.debug(msg)
  
  def has_permission(self, request, view):
    self.debug("Check permission: %s, %s" % (request.method, view))
    if request.method == "POST":
      return has_perms(request.user, view.model, PERM_WRITE)
    else:
      return True

  def has_object_permission(self, request, view, obj):
    self.debug("Check Object permissions %s, %s, %s" % (
      request.method,
      request.user,
      obj_to_namespace(obj)
    ))

    if request.method in permissions.SAFE_METHODS:
      return has_perms(request.user, obj, PERM_READ)
    else:
      return has_perms(request.user, obj, PERM_WRITE)

class PermissionedModelSerializer(serializers.ModelSerializer):
  def to_representation(self, instance):
    """
    Apply permissions to serialized data before sending it out for
    good
    """
    r = super(serializers.ModelSerializer, self).to_representation(instance)
    req = self.context.get("request",None)
    user = self.context.get("user")

    if not user and req:
      user = req.user

    if user:
      r = permissions_apply_to_serialized_model(
        instance,
        user,
        data=r
      )
    return r
