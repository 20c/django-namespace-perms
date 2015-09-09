# Purpose 

Provide granular permissions to django that go down to the level of individual model fields. For example we want to be able to grant a user permission to read the field "name" of a certain object instance

    app_name.model_name.instance_id.field_name

# Installation 

## Django

Edit settings.py INSTALLED_APPS

    INSTALLED_APPS += (
      "django_namespace_perms",
      "autocomplete_light"
    )

Run
   
    python manage.py syncdb

Edit urls.py and add 

    url(r'^autocomplete/',  include('autocomplete_light.urls')),

## Add Inline Permission editing to the user admin forms

Edit your app admin.py and add these:
  
    from django_namespace_perms.admin import UserAdmin

    admin.site.unregister(User)
    admin.site.register(User, UserAdmin)

Note that this will remove editing of django out-of-the-box permissions from the admin UI and replace it with the nsp permissions forms. So make sure you enable NSP as a django permissions backend (next step)

If you wish to simply append django namespace permissions forms the the user and group admin editors you can do so by adding UserGroupInline and UserPermissionInline to the existing UserAdmin admin model

    from django_namespace_perms.admin import (
      UserGroupInline, 
      UserGroupInlineAdd, 
      UserPermissionInline,
      UserPermissionInlineAdd
    )
    from django.contrib.auth.admin import UserAdmin
    from django.contrib.auth.models import User

    class UserAdmin(UserAdmin):
      ...
      inlines = (UserPermissionInline, UserPermissionInlineAdd)
      ...
    
    admin.site.register(User, UserAdmin)

## Set as django permission backend

Edit your settings.py and add 

    AUTHENTICATION_BACKENDS = ("django_namespace_perms.auth.backends.NSPBackend",)

## Supports Django REST Framework

Edit your settings.py and add

    REST_FRAMEWORK = {
      'DEFAULT_PERMISSION_CLASSES' : (
        'rest_framework.permissions.IsAuthenticated',
        'django_namespace_perms.rest.BasePermission',
      )
    }

Also you might need to add the same classes to permissions_classes property of the rest viewset class you defined in view.py

# Usage

## Permission namespace structure examples

Permissions for applications and models

give read access to all model instances that are part of application matching app-name

    app_name : PERM_READ

give read access to all fields on all models matching app-name.model-name

    app_name.model_name : PERM_READ

give write access to all fields on instance(id=1) of app-name.model-name

    app_name.model_name.1 : PERM_WRITE 

give write access to field field-name of instance(id=1) of app-name.model-name

    app_name.model_name.1.field_name : PERM_WRITE

deny access to field field-name on all model instances of app-name.model-name

    app_name.model_name.*.field_name : PERM_DENY

Permissions dont need to target application and model names, they can be completely arbitrary, like

    a.b : PERM_READ
    a.b.c : PERM_WRITE

## Checking permissions

    import django_namespace_perms.util as nsp
    from django_namespace_perms.constants import PERM_READ, PERM_WRITE
    from django.contrib.auth import User

    user = User.objects.get(id=1)

    #check if user has read perms to a model (User as example)

    nsp.has_perms(user, User, PERM_READ)

    #check if user has read perms to a model field (User.username as example)

    nsp.has_perms(user, [User, "username"], PERM_READ)

    #check if user has read perms to a model instance

    nsp.has_perms(user, user, PERM_READ)

    #check if user has read perms to arbitrary namespace

    nsp.has_perms(user, "a.b.c", PERM_READ)

    # When checking multiple perms for the same user, make sure to cache the perms
    # in order to speed up the process
    perms = nsp.load_perms(user)
    nsp.has_perms(perms, User, PERM_WRITE)
    nsp.has_perms(perms, SomeModel, PERM_READ)

## Building namespaces

By default the namespace for a model will be returned as 

    app_name.model_name

and the namespace for a model instance will be returned as

    app_name.model_name.<id>

Which is all you need in most cases, but sometimes it makes sense to customize your namespaces. For example when 
you wish to nest permissions

    class Parent(object):
      
      # we override the model instance's namespace
      # so it returns 'parent.<id>'

      @property
      def nsp_namespace(self):
        return "parent.%s" % self.id
    
    class Child(object):
      
      parent = models.ForeignKey(Parent)
      
      # we want child perms to be nested under it's parent
      # so again we override the namespace and prepend
      # the parent's namespace to it
      #
      # it returns 'parent.<parent_id>.child.<child_id>

      @property
      def nsp_namespace(self):
        return "%s.child.%s" % (self.parent.nsp_namespace, self.id)
          
Doing this can be really usefully if you want to quickly permission out sets of objects. So a user with
permissions to parent.1 would have also permissions to all child objects under that parent.

## Requiring explicit permissions

It's nice to be able to grant a user permissions to "parent" and automatically cascade those permissions
out to all the children under it, however sometimes this is too loose and you may want to restrict permissions
to certain children. 

In order to do this you need to require explicit permissions for a model (continuing from example above)
    
    class Child(object):
      ...
      
      # we require the user to have explicit perms to an
      # instance of the model for him to be allowed to write
      # to it

      @property
      def nsp_require_explicit_write(self):
         return True

This means that in order for the user to be able to write to an instance of Child he needs to have a permission
rule explicitly targeting either

    parent.<parent_id>.child.<child_id>  -> PERM_WRITE

or

    parent.*.child.*   -> PERM_WRITE

## Apply permissions to dict data

It is possible to apply a users permissions to a data dict, removing any keys the user does not have permission to see.

Let's assume the user has permissions set as follows

    a.b : READ
    a.b.c : READ | WRITE
    a.b.d : DENY
    b : READ

We can apply these permissions to any dict holding data with the proper keys

    data = {
      "a" : {
        "b": {
          "c" : "This should be here",
          "d" : "This should be gone"
        }
      },
      "b" : "This should be here",
      "c" : "This should be gone"
    }

    from django_namespace_perms.util import perms_structure, permissions_apply

    data = permissions_apply(data, perms_structure(user))

After permissions apply the contents of data will be

    {
      "a" : {
        "b" : {
          "c" : "This should be here"
        }
      },
      "b" : "This should be here"
    }

### Applying permissions to lists

If you have a dataset that looks like this

    data = {
      "a" : [
        { "id" : 1, "name" : "should be here" },
        { "id" : 2, "name" : "should be gone" }
      ]
    }

you can still apply permissions to it, but it's a bit trickier. In order to do so you will need to
define a list-handler

    # we want the list handler function to return the id of the row
    # since this is what we want to append to the namspace
    # 
    # so each row in the list will be checked against the namespace
    # a.<row.id>

    def handler(**kwargs):
      return kwargs.get("id")

    ruleset = {
      "list-handlers" : {
        # namespace a
        "a" : {
          namespace : handler
        }
      }
    }

    data = permissions_apply(data, perms_structure(user), ruleset=ruleset)


## Setting permissions via API

    from django_namespace_perms.constants import PERM_READ, PERM_WRITE
    from django_namespace_perms.models import GroupPermission, UserPermission
    from django_namespace_perms.util import obj_to_namespace
    from django.contrib.auth.models import User, Group

    # adding a new group permission to group with id=1
    group = Group.objects.get(id=1)
    perm = GroupPermission(group=group, namespace="a.b.c", permissions=PERM_READ)
    perm.save()

    # adding a new user permission to user with id=1]
    user = User.objects.get(id=1)
    perm = UserPermission(user=user, namespace="a.b.c", permissions=PERM_WRITE)
    perm.save()

    # use obj_to_namespace to quickly permission out models or instances
    perms = UserPermission(user=user, namespace=obj_to_namespace(SomeModel), permission=PERM_READ)
    perms = UserPermission(user=user, namespace=obj_to_namespace(SomeModel.objects.get(id=1)), permission=PERM_WRITE)


## discover permission namespaces (which then can be granted/revoked in the admin ui)

    from django_namespace_perms.util import autodiscover_namespaces

    autodiscover_namespaces(SomeModel)


# Known Issues

Autocomplete in admin interface for auto-discovered namespaces does currently not work if grappeli is installed.
