# INSTALLATION

Edit settings.py INSTALLED_APPS

    INSTALLED_APPS += (
      "django_namespace_perms",
      "autocomplete_light"
    )

Run
   
    python manage.py syncdb

# Add Inline Permission editing to the user admin forms

Edit your apps admin.py
  
    from django_namespace_perms.admin import UserGroupInline, UserPermissionInline

    class UserAdmin(UserAdmin):
      ...
      inlines = (UserGroupInline, UserPermissionInline)
      ...

# Usage

## Perm namespace structure examples

Permissions for applications and models

    app_name : PERM_READ -> gives read access to all model instances that are part of application app_name
    app_name.model_name : PERM_READ -> gives read access to all fields on all models matching app_name.model_name
    app_name.model_name.1 : PERM_WRITE -> gives write access to all fields on instance(id=1) of app_name.model_name
    app_name.model_name.1.field_name : PERM_WRITE -> gives write access to field field_name of instance(id=1) of app_name.model_name
    app_name.model_name.*.field_name : PERM_DENY -> denies access to field field_name on all model instances of app_name.model_name

Permissions dont need to target application and model names, they can be completely custom like

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

    nsp.has_perms(user, User._meta.get_field_by_name("username"), PERM_READ)

    # When checking multiple perms for the same user, make sure to cache the perms
    # in order to speed up the process
    perms = nsp.load_perms(user)
    nsp.has_perms(perms, User, PERM_WRITE)
    nsp.has_perms(perms, SomeModel, PERM_READ)


## discover permission namespaces (which then can be granted/revoked in the admin ui)

    from django_namespace_perms.util import autodiscover_namespaces

    autodiscover_namespaces(SomeModel)

# Set as django permission backend

Edit your settings.py and add 

    AUTHENTICATION_BACKENDS = ("django_namespace_perms.auth.backends.NSPBackend",)

# Integrate into django rest framework

Edit your settings.py and add

    REST_FRAMEWORK = {
      'DEFAULT_PERMISSION_CLASSES' : (
        'rest_framework.permissions.IsAuthenticated',
        'django_namespace_perms.rest.BasePermission',
      )
    }

Also you might need to add the same classes to permissions_classes property of the rest viewset class you defined in view.py
