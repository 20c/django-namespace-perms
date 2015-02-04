# Installation 

## Django

Edit settings.py INSTALLED_APPS

    INSTALLED_APPS += (
      "django_namespace_perms",
      "autocomplete_light"
    )

Run
   
    python manage.py syncdb

## Add Inline Permission editing to the user admin forms

Edit your app admin.py and add these:
  
    from django_namespace_perms.admin import UserAdmin

    admin.site.unregister(User)
    admin.site.register(User, UserAdmin)

Note that this will remove editing of django out-of-the-box permissions from the admin UI and replace it with the nsp permissions forms. So make sure you enable NSP as a django permissions backend (next step)

If you wish to simply append django namespace permissions forms the the user and group admin editors you can do so by adding UserGroupInline and UserPermissionInline to the existing UserAdmin admin model

    from django_namespace_perms.admin import UserGroupInline, UserPermissionInline
    from django.contrib.auth.admin import UserAdmin
    from django.contrib.auth.models import User

    class UserAdmin(UserAdmin):
      ...
      inlines = (UserGroupInline, UserPermissionInline)
      ...
    
    admin.site.register(User, UserAdmin)

## Set as django permission backend

Edit your settings.py and add 

    AUTHENTICATION_BACKENDS = ("django_namespace_perms.auth.backends.NSPBackend",)

## Integrate into django rest framework

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

    nsp.has_perms(user, User._meta.get_field_by_name("username"), PERM_READ)

    #check if user has read perms to arbitrary namespace

    nsp.has_perms(user, "a.b.c", PERM_READ)

    # When checking multiple perms for the same user, make sure to cache the perms
    # in order to speed up the process
    perms = nsp.load_perms(user)
    nsp.has_perms(perms, User, PERM_WRITE)
    nsp.has_perms(perms, SomeModel, PERM_READ)


## discover permission namespaces (which then can be granted/revoked in the admin ui)

    from django_namespace_perms.util import autodiscover_namespaces

    autodiscover_namespaces(SomeModel)


# Known Issues

Autocomplete in admin interface for auto-discovered namespaces does currently not work if grappeli is installed.
