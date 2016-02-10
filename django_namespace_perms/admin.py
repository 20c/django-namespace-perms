
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User, Group 

from django_namespace_perms.models import perm_choices, GroupPermission, UserPermission
from django_namespace_perms.constants import *
from django_namespace_perms.util import NAMESPACES, nsp_mode

from django import forms
from django.db import models
from django.conf import settings

import autocomplete_light

def assign_group_to_all_users(modeladmin, request, queryset):
  User = get_user_model()
  users = User.objects.all()
  for group in queryset:
    #note: cant do bulk_save here since right now that doesnt trigger the save signal,
    #revist when/if that get's fixed
    for user in users:
      group.user_set.add(user)
assign_group_to_all_users.short_description = "Assign selected groups to all users"


def revoke_group_from_all_users(modeladmin, request, queryset):
  for group in queryset:
    group.user_set.remove(user)
revoke_group_from_all_users.short_description = "Revoke selected groups from all users"

class BitmaskSelectMultiple(forms.CheckboxSelectMultiple):
  outer_html = '<div{id_attr}>{content}</div>'
  inner_html = '<span style="margin-right:15px">{choice_value}{sub_widgets}</span>'
  
  def __init__(self, *args, **kwargs):
    super(BitmaskSelectMultiple, self).__init__(*args, **kwargs)
    self.renderer.outer_html = self.outer_html
    self.renderer.inner_html = self.inner_html

  def render(self, name, value, attrs=None):
    values = []
    if type(value) == list:
      i = 0
      for v in value:
        i = i | int(v)
      value = i
    for p,lbl in perm_choices():
      if value & p != 0:
        values.append(p)
    return super(BitmaskSelectMultiple, self).render(name, values, attrs=attrs)
  def value_from_datadict(self, data, files, name):
    i = 0
    for p in data.getlist(name):
      i = i | int(p)
    return i

# Register your models here.

class NamespaceAutocomplete(autocomplete_light.AutocompleteListBase):
  choices = [v for k,v in NAMESPACES]
autocomplete_light.register(NamespaceAutocomplete);

class PermissionForm(forms.Form):
  def clean_permissions(self):
    perms = self.cleaned_data["permissions"]
    if type(perms) == list:
      i = 0
      for p in perms:
        i = i | int(p)
      perms = i
    return int(perms)


class ManualUserPermissionInline(autocomplete_light.ModelForm, PermissionForm):
  class Meta:
    model = UserPermission
    widgets = {
      'namespace' : autocomplete_light.TextWidget('NamespaceAutocomplete', attrs={"style":"width:500px"}),
      'permissions' : BitmaskSelectMultiple(choices=perm_choices())
    }
    fields = "__all__"




class ManualGroupPermissionInline(autocomplete_light.ModelForm, PermissionForm):
  class Meta:
    model = GroupPermission
    widgets = {
      'namespace' : autocomplete_light.TextWidget('NamespaceAutocomplete', attrs={"style":"width:500px"}),
      'permissions' : BitmaskSelectMultiple(choices=perm_choices())
    }
    fields = "__all__"

class GroupPermissionAdmin(admin.ModelAdmin):
  list_display = ('group', 'namespace', 'permissions')

class GroupPermissionInline(admin.TabularInline):
  model = GroupPermission
  form = ManualGroupPermissionInline
  fields = ("namespace", "permissions")
  readonly_fields = ["namespace"]

  def has_add_permission(self, request):
    return False

class GroupPermissionInlineAdd(admin.TabularInline):
  model = GroupPermission
  form = ManualGroupPermissionInline
  verbose_name_plural = "Add group permissions"

  def has_change_permission(self, request, obj=None):
    return False


class UserPermissionInline(admin.TabularInline):
  model = UserPermission
  form = ManualUserPermissionInline
  fields = ("namespace", "permissions")
  readonly_fields = ["namespace"]

  def has_add_permission(self, request):
    return False

class UserPermissionInlineAdd(admin.TabularInline):
  model = UserPermission
  form = ManualUserPermissionInline
  verbose_name_plural = "Add user permissions"

  def has_change_permission(self, request, obj=None):
    return False


class GroupAdmin(admin.ModelAdmin):
  list_display = ('name',)
  search_fields = ('name',)
  #remove default permissions form
  exclude = ('permissions',)
  inlines = (GroupPermissionInline, GroupPermissionInlineAdd)
  actions = [
    assign_group_to_all_users,
    revoke_group_from_all_users
  ]

class UserAdmin(DjangoUserAdmin):
  inlines = (UserPermissionInline, UserPermissionInlineAdd)
  add_fieldsets = (
    (None, {
        'classes' : ('wide',),
        'fields' : ('username' ,'password1', 'password2', 'email')
    })
  )

  def __init__(self, *args, **kwargs):
    DjangoUserAdmin.__init__(self, *args, **kwargs)
    # remove default permissions forms
    for label, fieldset in self.fieldsets:
      fieldset["fields"] = [x for x in fieldset["fields"] if x not in [
        'user_permissions'
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
