import re
import constants

APP_NAMESPACES = [
]

NAMESPACES = [
]

#############################################################################

def autodiscover_namespaces(*models):
  for model in models:
    ns = "%s.%s" % (model._meta.app_label, model._meta.model_name)
    NAMESPACES.append((ns,ns))
    if model._meta.app_label not in APP_NAMESPACES:
      APP_NAMESPACES.append(model._meta.app_label)
    for field in model._meta.fields:
      fld = field.name
      ns_ = "%s.*.%s" % (ns, fld)
      NAMESPACES.append((ns_, ns_))
  for app_ns in APP_NAMESPACES:
    NAMESPACES.append((app_ns, app_ns))
  NAMESPACES.sort()

#############################################################################

def load_perms(user):
  
  if hasattr(user, "_nsp_perms"):
    user._nsp_perms_struct = perms_structure(user._nsp_perms)
    return user._nsp_perms

  from django_namespace_perms.models import UserPermission, GroupPermission
  from django.conf import settings
  from django.core.exceptions import ObjectDoesNotExist
  from django.contrib.auth.models import Group

  if user.is_authenticated():
    perms = UserPermission.objects.filter(user=user)
    group_perms = GroupPermission.objects.filter(group__in=user.groups.all())
  else:
    # guest user
    if hasattr(settings, "NSP_GUEST_GROUP"):
      guest_group = settings.NSP_GUEST_GROUP
    else:
      guest_group = "Guest"
    try:
      group = Group.objects.get(name=guest_group)
      group_perms = GroupPermission.objects.filter(group=group)
    except ObjectDoesNotExist:
      group_perms = []
    perms = []

  permdict = {}
  for perm in group_perms:
    permdict[perm.namespace] = perm.permissions
  for perm in perms:
    permdict[perm.namespace] = perm.permissions

  print permdict

  user._nsp_perms = permdict
  user._nsp_perms_struct = perms_structure(permdict)

  return permdict

#############################################################################

def permcode_to_namespace(perm):
  label, perm_code = tuple(perm.split("."))
  a = re.match("(add|delete|change|view)_(.+)", perm_code)

  if a:
    if a.group(1) == "view":
      return ("%s.%s.%s" % (label, a.group(2), a.group(1)), constants.PERM_READ)
    else:
      return ("%s.%s.%s" % (label, a.group(2), a.group(1)), constants.PERM_WRITE)

  return (label, constants.PERM_READ)



#############################################################################

def obj_to_namespace(obj):
  namespace = str(obj)
  if hasattr(obj, "nsp_namespace"):
    return  obj.nsp_namespace.lower()

  if type(obj) == list:
    if len(obj) != 2:
      raise Exception("When passing a list to obj_to_namespace it is expected to have two items: The model instance and the field name")
    ns = "%s.%s" % (obj_to_namespace(obj[0]), obj[1].lower())
    return ns

  if hasattr(obj, "db_column") and hasattr(obj, "model"):
    namespace = "%s.%s.%s" % (
      obj.model._meta.app_label, 
      obj.model._meta.model_name,
      obj.name
    )
  elif hasattr(obj, "_meta"):
    namespace = "%s.%s" % (
      obj._meta.app_label, 
      obj._meta.model_name
    )
  if hasattr(obj, "id"):
    namespace = "%s.%s" % (namespace, obj.id)
 

  return namespace.lower()



#############################################################################

def has_perms(user, namespace, level, ambiguous=False):
  
  if type(namespace) not in [str, unicode]:
    namespace = obj_to_namespace(namespace)

  if type(user) != dict:
    if user.is_superuser:
      return True
    perms = load_perms(user)
  else:
    perms = user

  return ((check_perms(perms, namespace, ambiguous=ambiguous) & level) != 0)


#############################################################################

def check_perms(perms, prefix, ambiguous=False):

  """
  Return the user's perms for the specified prefix

  perms <dict> permissions dict
  prefix <string> namespace to check for perms

  ambiguous <bool=False> if True reverse wildcard matching is active and a perm check for a.b.* will
  be matched by the user having perms to a.b.c or a.b.d - only use this if you know what 
  you are doing.
  """

  try:

    token = prefix.split(".")

    i = 1
    l = len(token)
    r = 0

    # collect permission rules with a wildcard in them, so we dont do unecessary
    # regex searches later on
    perms_wc = {}
    for ns, p in perms.items():
      if ns.find("*") > -1:
        perms_wc[re.escape(ns).replace("\*", "[^\.]+")] = p

    while i <= l:
      k = ".".join(token[:i])
      matched = False

      # check for exact match
      if perms.has_key(k):
        r = perms.get(k)

      # check for wildcard matches (if any wildcard rules exist)
      elif perms_wc:
        for ns, p in perms_wc.items():
          a = "^%s$" % ns
          b = "^%s\." % ns
          j = len(a)
          u = len(b)
          if j > matched and re.match(a, k):
            r = p
            matched = j
          elif u > matched and re.match(b, k):
            r = p
            matched = u

      # if not matched at all and ambiguous flag is true, do ambiguous matching
      if not matched and ambiguous:
        m = "^%s" % re.escape(k).replace("\*", "[^\.]+")
        for ns, p in perms.items():
          if re.match(m, ns) and p > r:
            r = p
            break

      i += 1

    return r
  except:
    raise  

###############################################################################

def permissions_apply_additive(data, perms_struct):
  if not perms_struct:
    return {}

  if type(perms_struct) != dict or type(data) != dict:
    return data

  rv = {}
  for k,v in data.items():
    if perms_struct.get(k):
      rv[k] = permissions_apply_additive(v, perms_struct.get(k))
    if perms_struct.get("@%s"%k):
      d = permissions_apply_additive(v, perms_struct.get("@%s"%k))
      if type(d) == dict and type(rv.get(k)) == dict:
        rv[k].update(d)
      else:
        rv[k] = d
    if perms_struct.get("*"):
      d = permissions_apply_additive(v, perms_struct.get("*"))
      if type(d) == dict and type(rv.get(k)) == dict:
        rv[k].update(d)
      else:
        rv[k] = d

  return rv

#############################################################################

def permissions_apply_subtractive(data, perms_struct):
  for k,p in perms_struct.items():
    if k[0] == "@":
      k = k[1:]
    if data.has_key(k):
      if not p or (type(data[k]) == dict and not any(data[k])):
        del data[k]
      elif type(p) == dict:
        permissions_apply_subtractive(data.get(k), p)
    elif k == "*":
      for n,v in data.items():
        if not p or (type(data[n]) == dict and not any(data[n])):
          del data[n]
        elif type(p) == dict:
          permissions_apply_subtractive(v, p)

#############################################################################

def permissions_apply(data, perms_struct, path=''):
  if type(perms_struct) != dict:
    load_perms(perms_struct)
    perms_struct = perms_struct._nsp_perms_struct

  rv = permissions_apply_additive(data, perms_struct)
  permissions_apply_subtractive(rv, perms_struct)
  return rv

#############################################################################

def permissions_apply_to_serialized_model(smodel, perms_struct):
  inst = smodel.instance
  namespace = obj_to_namespace(inst).split(".")
  structure = d = {}
  l = len(namespace)
  i = 0
  print namespace
  while i < l:
    k = namespace[i]
    if i < l-1:
      d[k] = {}
      d = d[k]
    else:
      d[k] = smodel.data
    i += 1


  r = permissions_apply(
    structure,
    perms_struct
  )

  print r

  for k in namespace:
    print k, r
    r = r[k]

  return r

#############################################################################

def perms_structure(perms):
  perms_wc = {}
  for ns, p in perms.items():
    pieces = ns.split(".")
    a = prev = perms_wc 
    n = 0 
    l = len(pieces)
    for k in pieces:
      if n < l-1:
        if not a.has_key(k):
          a[k] = {}
        elif type(a[k]) != dict:
          a["@%s"%k] = a[k]
          a[k] = {}
        a = a[k]
      else:
        if not a.has_key(k):
          a[k] = p
        else:
          a["@%s"%k] = p
      n += 1
   

  return perms_wc 
