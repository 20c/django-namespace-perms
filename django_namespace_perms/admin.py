
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from django_namespace_perms.models import Group, GroupPermission, UserPermission, UserGroup
from django_namespace_perms.constants import *
from django_namespace_perms.util import NAMESPACES

from django import forms

import autocomplete_light

def assign_group_to_all_users(modeladmin, request, queryset):
  User = get_user_model()
  users = User.objects.all()
  for group in queryset:
    #note: cant do bulk_save here since right now that doesnt trigger the save signal,
    #revist when/if that get's fixed
    for user in users:
      ug = UserGroup(user=user, group=group)
      ug.save()
assign_group_to_all_users.short_description = "Assign selected groups to all users"


def revoke_group_from_all_users(modeladmin, request, queryset):
  UserGroup.objects.filter(group__in=queryset).delete()
revoke_group_from_all_users.short_description = "Revoke selected groups from all users"



# Register your models here.

class NamespaceAutocomplete(autocomplete_light.AutocompleteListBase):
  choices = [v for k,v in NAMESPACES]
autocomplete_light.register(NamespaceAutocomplete);

class ManualUserPermissionInline(autocomplete_light.ModelForm):
  class Meta:
    model = UserPermission
    widgets = {
      'namespace' : autocomplete_light.TextWidget('NamespaceAutocomplete', attrs={"size":50})
    }
    fields = "__all__"

class ManualGroupPermissionInline(autocomplete_light.ModelForm):
  class Meta:
    model = GroupPermission
    widgets = {
      'namespace' : autocomplete_light.TextWidget('NamespaceAutocomplete', attrs={"size":50})
    }
    fields = "__all__"


class GroupPermissionAdmin(admin.ModelAdmin):
  list_display = ('group', 'namespace', 'permissions')

class GroupPermissionInline(admin.TabularInline):
  model = GroupPermission
  form = ManualGroupPermissionInline

class UserPermissionInline(admin.TabularInline):
  model = UserPermission
  form = ManualUserPermissionInline

class UserGroupInline(admin.TabularInline):
  model = UserGroup

class GroupAdmin(admin.ModelAdmin):
  list_display = ('name',)
  search_fields = ('name',)
  #remove default permissions form
  exclude = ('permissions',)
  inlines = (GroupPermissionInline,)
  actions = [
    assign_group_to_all_users,
    revoke_group_from_all_users
  ]

class UserAdmin(DjangoUserAdmin):
  inlines = (UserGroupInline, UserPermissionInline,)
  add_fieldsets = (
    (None, {
        'classes' : ('wide',),
        'fields' : ('username' ,'password1', 'password2', 'email')
    }),
  )

  def __init__(self, *args, **kwargs):
    DjangoUserAdmin.__init__(self, *args, **kwargs)
    # remove default permissions forms
    for label, fieldset in self.fieldsets:
      fieldset["fields"] = [x for x in fieldset["fields"] if x not in [
        'groups', 'user_permissions'
      ]]

try:
  admin.site.unregister(Group)
except:
  pass
admin.site.register(Group, GroupAdmin)
try:
  admin.site.unregister(User)
except:
  pass
admin.site.register(User, UserAdmin)
