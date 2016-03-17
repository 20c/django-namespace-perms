from django.contrib.auth.models import User;
from django.contrib.auth.backends import ModelBackend

from django_namespace_perms.constants import *
from django_namespace_perms.util import (
  NAMESPACES, 
  obj_to_namespace, 
  permcode_to_namespace, 
  has_perms, 
  load_perms
)

import logging
import re

log = logging.getLogger("django")

# Admin namespace prefixes

# Grant perms to a namespace
ADMIN_NS_GRANT = "admin.grant"

class NSPBackend(ModelBackend):

  """
  Authenticate actions using nsp
  """

  def load_perms(self, user_obj):
    return load_perms(user_obj)

  def has_module_perms(self, user_obj, obj=None):
    if hasattr(obj, "nsp_namespace"):
      fn = getattr(obj, "nsp_namespace")
      if not callable(fn):
        raise Exception("nsp_namespace attribute needs to be callable for %s" % obj)
      namespace = fn()
    else:
      namespace = obj_to_namespace(obj)

    log.info("Checking module perms: %s" % namespace)
    
    perms = self.load_perms(user_obj)

    return has_perms(perms, namespace, PERM_READ)

  def has_perm(self, user_obj, perm, obj=None):

    #if not user_obj.is_authenticated() or not user.is_active:
      #FIXME: load guest perms and proceed
    #  return False

    # super users have access to everything
    if user_obj.is_superuser:
      return True

    namespace, level = permcode_to_namespace(perm)

    write_ops = ["add", "delete", "change"]
    if hasattr(obj, "nsp_write_ops") and callable(obj, "nsp_write_ops"):
      write_ops.extend(getattr(obj, "nsp_write_ops")())

    log.info( "NSP has_perms %s %s %s" % (namespace, perm, level))

    perms = self.load_perms(user_obj)

    return has_perms(perms, namespace, level)
