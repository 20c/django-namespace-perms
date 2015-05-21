import django_namespace_perms.util as nsp
from django_namespace_perms.constants import PERM_READ, PERM_WRITE

from django import template

register = template.Library()

@register.filter
def nsp_check_write(user, obj):
  return nsp.has_perms(user, obj, PERM_WRITE)

@register.filter
def nsp_check_read(user, obj):
  return nsp.has_perms(user, obj, PERM_READ)
