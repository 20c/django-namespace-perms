
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group

from django_namespace_perms.constants import *
from django_namespace_perms.util import NAMESPACES

#############################################################################

#class Group(models.Model):
#  name = models.CharField(max_length=255, unique=True)
#
#  class Meta:
#    db_table = u'nsp_group'
#
#  def __unicode__(self):
#    return self.name

#############################################################################

class GroupPermission(models.Model):
  group = models.ForeignKey(Group, blank=False)
  namespace = models.CharField(max_length=255, blank=False)
  permissions = models.IntegerField(choices=PERM_CHOICES, blank=False, default=PERM_READ)

  class Meta:
    db_table = u'nsp_group_permission'

  def __unicode__(self):
    return "%s: %s" % (self.group.name, self.namespace)

  def xbahn_replicate_relations(self):
    return {"group" : ("id", "name")}

#############################################################################

class UserPermission(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False)
  namespace = models.CharField(max_length=255, blank=False)
  permissions = models.IntegerField(choices=PERM_CHOICES, blank=False, default=PERM_READ)

  class Meta:
    db_table = u'nsp_user_permission'

  def __unicode__(self):
    return "%s: %s" % (self.user.username, self.namespace)

#############################################################################

class UserGroup(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False)
  group = models.ForeignKey(Group, blank=False)

  class Meta:
    db_table = u'nsp_user_group'
    unique_together = ('user', 'group')

  def xbahn_replicate_relations(self):
    return {"group" : ("id", "name")}

  def __unicode__(self):
    return "%s: %s" % (self.user.username, self.group.name)

#############################################################################

if hasattr(settings, 'XBAHN') and settings.XBAHN.get("replication") and "namespace_perms" in settings.XBAHN["replication"].get("replicate",[]):
    import twentyc.xbahn.django.replication as replication
    replication.replicate(
      UserPermission,
      GroupPermission,
      UserGroup
    )
