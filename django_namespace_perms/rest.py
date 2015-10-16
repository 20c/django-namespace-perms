from rest_framework import permissions, serializers

from django_namespace_perms.util import (
  has_perms, 
  obj_to_namespace,
  permissions_apply_to_serialized_model
)

from django_namespace_perms.constants import PERM_READ, PERM_WRITE 
import logging
from exceptions import PermissionDenied


log = logging.getLogger(__name__)

class BasePermission(permissions.BasePermission):

  def debug(self, msg):
    print msg
    log.debug(msg)
  
  def has_permission(self, request, view):
    """
    self.debug("Check permission: %s, %s" % (request.method, view.model))
    if request.method == "POST":
      return has_perms(request.user, view.model, PERM_WRITE)
    else:
      return True
    """
    # since instance of object does not exist yet and we have no access to the
    # serializer data we need to handle POST permission checks during
    # PermissionedModelSerializer.create - always return true here.
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
      func_name = "nsp_has_perms_%s" % request.method
      if hasattr(obj, func_name):
        func = getattr(obj, func_name)
        return func(request.user, request)
      else:
        return has_perms(request.user, obj, PERM_WRITE)

class PermissionedModelSerializer(serializers.ModelSerializer):

  def has_create_perms(self, user, validated_data):
      return has_perms(user, self.nsp_namespace_create(validated_data), PERM_WRITE)

  def create(self, validated_data):
    if hasattr(self, "nsp_namespace_create"):
      user = self.context.get("request").user
      if not user:
        raise PermissionDenied("User not set in serializer context")
      if self.has_create_perms(user, validated_data):
        return serializers.ModelSerializer.create(self, validated_data)
      else:
        raise PermissionDenied("User does not have write permissions to '%s'" % self.nsp_namespace_create(validated_data))
    else:
      raise PermissionDenied("Serializer missing classmethod '%s' - so we have no way to determine permissioning namespace for instance creation" % "nsp_namespace_create")
      

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
      
      # superusers can see everything
      if user.is_superuser:
        return r

      if getattr(instance, "nsp_require_explicit_read", False):
        if not has_perms(user, instance, 0x01):
          return None 

      r = permissions_apply_to_serialized_model(
        instance,
        user,
        data=r
      )
    return r
