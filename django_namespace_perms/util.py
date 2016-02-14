import re
import constants
import json
import inspect

from django.db.models.query import QuerySet
from django.conf import settings


APP_NAMESPACES = [
]

NAMESPACES = [
]

WRITE_OPS = [
  "update",
  "change",
  "delete",
  "create",
  "add"
]

STR_TYPES = [str, unicode]

#############################################################################

def nsp_mode():
  return getattr(settings, "NSP_MODE", "rw")

#############################################################################

def get_permission_flag(op):
  """
  Returns the approporiate permission flag for the operation passed
  in op

  valid operation values:
    - "read" or "view"
    - "create" or "add"
    - "update" or "change"
    - "delete"
  """

  mode = getattr(settings, "NSP_MODE", "rw")

  if op in WRITE_OPS:
    if mode == "crud":
      if op == "create" or op == "add":
        return constants.PERM_CREATE
      elif op == "update" or op == "change":
        return constants.PERM_UPDATE
      elif op == "delete":
        return constants.PERM_DELETE
    else:
      return constants.PERM_WRITE
  else:
    return constants.PERM_READ


#############################################################################

class PermissionFrame(object):
  def __init__(self, p):
#    print "PermissionFrame", p
    self.value = p

  def has_value(self):
    return (self.value is not None)

  def check(self, level):
    if self.value is None:
      return False
    return (self.value & level) == level

#############################################################################

def dict_valid(v):
  return hasattr(v, "items") and callable(v.items)

def dict_from_namespace(keys, data):
  if type(keys) != list:
    keys = keys.split(".")
  root = p = d = {}
  j = 0
  for k in keys:
    d[k] = {}
    p = d
    d = d[k]
  p[k] = data
  return root

def dict_has_value(data, value):
  if data == value:
    return True
  for k, item in data.items():
    return dict_has_value(item, value)
  return False

def dict_get_path(data, keys):
  for k in keys:
    if data.has_key(k):
      data = data[k]
    else:
      return None
  return data


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
  if hasattr(user, "nsp_manual"):
    for ns,p in user.nsp_manual.items():
      permdict[ns] = p
  for perm in group_perms:
    permdict[perm.namespace] = perm.permissions
  for perm in perms:
    permdict[perm.namespace] = perm.permissions

  user._nsp_perms = permdict
  user._nsp_perms_struct = perms_structure(permdict)

  return permdict

#############################################################################

def permcode_to_namespace(perm):
  label, perm_code = tuple(perm.split("."))
  a = re.match("(add|delete|change|view)_(.+)", perm_code)

  if a:
    return ("%s.%s.%s" % (label, a.group(2), a.group(1)), get_permission_flag(a.group(1)))

  return (label, get_permission_flag("read"))



#############################################################################

def obj_to_namespace(obj):
  namespace = str(obj)

  if inspect.isclass(obj):
    # class passed check existance of possible class methods
    if hasattr(obj, "nsp_namespace_create"):
      return obj.nsp_namespace_create().lower()
    elif hasattr(obj, "nsp_namespace_base"):
      return obj.nsp_namespace_base().lower()

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

def has_perms(user, namespace, level, ambiguous=False, explicit=False):

  """
  Check if a user has perms to the specified name space.

  This should be the primary function you call to check if a user has access to
  something.

  user <dict|AUTH_USER_MODEL> - the user's permissions, can be a perm_structure dict
  a load_perms dict or the User model itself. Passing the user model may force a call
  of load_perms if they had not been loade yet.

  namespace <string|ModelInstance|list> - the namespace to check, can be the namespace
  string itself, the instance of a django model or a list holding the instance of a
  django model at index 0 and a model field name at index 1

  level <int|str> - permission level to check, if passed as string any value that
  is valid to be passed to get_permission_flag is ok

  explicit <bool=False> - if true, explicit permissions are required to the
  full path provided in namespace, partial namespace matches will be ignored.
  """

  if type(level) in STR_TYPES:
    level = get_permission_flag(level)

  if type(namespace) not in STR_TYPES:
    
    if level == constants.PERM_READ and hasattr(namespace, "nsp_require_explicit_read"):
      explicit = namespace.nsp_require_explicit_read
    elif level == constants.PERM_WRITE and hasattr(namespace, "nsp_required_explicit_write"):
      explicit = namespace.nsp_require_explicit_write

    namespace = obj_to_namespace(namespace)

  if type(user) != dict:
    if user.is_superuser:
      return True
    perms = load_perms(user)
    permstruct = user._nsp_perms_struct
  else:
    perms = user
    if not perms.has_key("__ps"):
      permstruct = perms_structure(perms)
    else:
      permstruct = perms

  return get_perms(permstruct, namespace.split("."), explicit=explicit).check(level)


#############################################################################

def check_perms(perms, prefix, ambiguous=False):

  """
  DEPRECATED - replaced by get_perms

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
  
  if not dict_valid(perms_struct) or not dict_valid(data):
    return data
  
  rv = {}
  for k,v in data.items():
    direct_match = False
    if perms_struct.get(k):
      pv = perms_struct.get(k)
      rv[k] = permissions_apply_additive(
        v, 
        pv
      )
      if type(pv) in (int,long) and pv > 0:
        direct_match = True

    if perms_struct.get("@%s"%k):
      d = permissions_apply_additive(
        v, 
        perms_struct.get("@%s"%k)
      )
      if dict_valid(d) and dict_valid(rv.get(k)):
        rv[k].update(d)
      else:
        rv[k] = d
    if not direct_match and perms_struct.get("*"):
      d = permissions_apply_additive(
        v, 
        perms_struct.get("*")
      )
      if dict_valid(d) and dict_valid(rv.get(k)):
        rv[k].update(d)
      else:
        rv[k] = d

  return rv

#############################################################################

def permissions_apply_subtractive(data, perms_struct, debug=False):
  if not dict_valid(data):
    raise Exception("Wanted a dict or dict-like object got %s" % type(data))

  for k,p in perms_struct.items():
    if k[0] == "@":
      k = k[1:]

    if data.has_key(k):

      if not p or (dict_valid(data[k]) and not any(data[k])):
        del data[k]
      elif type(data[k]) == dict and type(p) == dict:
        permissions_apply_subtractive(
          data.get(k), 
          p, 
          debug=debug
        )
        
    elif k == "*":
      for n,v in data.items():
        if not p or (dict_valid(data[n]) and not any(data[n])):
          del data[n]
        elif dict_valid(p) and dict_valid(v):
          permissions_apply_subtractive(
            v, 
            p, 
            debug=debug
          )

#############################################################################

def get_perms(d, keys, explicit=False):
  t = type(d)

  #print "checking for",keys,"in",d,explicit

  if t == int or t == long:
    if explicit and keys:
      return PermissionFrame(None)
    return PermissionFrame(d)
  if not keys:
    return PermissionFrame(None)

  r_a = 0 
  r_b = 0
  k = keys[0]
  if d.has_key(k):
    r_a = get_perms(d[k], keys[1:], explicit=explicit)
    if r_a.has_value():
      return r_a

  if d.has_key("@%s" % k):
    r_c = get_perms(d["@%s" % k], keys[1:], explicit=explicit)
    if r_c.has_value():
      return r_c
  
  if d.has_key("*"):
    r_b = get_perms(d["*"], keys[1:], explicit=explicit)
    if r_b.has_value():
      return r_b

  return PermissionFrame(None)
 

def perms_struct_has_explicit_rule(d, keys, level):
  return get_perms(d, keys, explicit=True).check(level)
 
#############################################################################

def permissions_apply_ruleset_require_explicit(data, path, perm, perms_struct, full_path=None):
  d = data
  j = p = None
  a = 0
  
  if type(path) is not list:
    keys = path.split(".")
  else:
    keys = path

  for k in keys:
    if k == "*":
      if not dict_valid(d):
        return
      for i,j in d.items():
        permissions_apply_ruleset_require_explicit(
          j, keys[a+1:], perm, perms_struct, full_path=keys[:a]+[i]
        )
      return
    else:
      if dict_valid(d) and d.has_key(k):
        p = (d,k)
        d = d[k]
      else:
        return

    a += 1
  if full_path is None:
    r = perms_struct_has_explicit_rule(perms_struct, keys, perm)
  else:
    r = perms_struct_has_explicit_rule(perms_struct, full_path + keys, perm)
  if not r and p:
    del p[0][p[1]]
    

#############################################################################

def permissions_apply_list_handler(data, path, handler, perms_struct, ruleset={}, full_path=None, container=None):

  d = data
  a = 0
  
  if type(path) is not list:
    keys = path.split(".")
  else:
    keys = path

  l = len(keys)

  for k in keys:
    if k == "*":
      if dict_valid(d): 
        for i,j in d.items():
          
          if a < l-1:
            _keys = keys[a+1:]
          else:
            _keys = []
          permissions_apply_list_handler(
            j, _keys, handler, perms_struct, full_path=keys[:a]+[i],container=(d,i), ruleset=ruleset
          )
        return
      elif type(d) is not list:
        return
    else:
      if dict_valid(d) and d.has_key(k):
        container = (d,k)
        d = d[k]
      else:
        return

    a += 1

  if d:
    n = []
    rs = {}
    if ruleset.has_key("require"):
      rs.update(require=ruleset.get("require"))
    rs.update(handler.get("ruleset",{}))
    if full_path:
      _path = full_path + keys
    else:
      _path = keys

    for item in d:
     
      if dict_valid(item):
        final_path = handler.get("namespace")(**item).lower().split(".")
      else:
        final_path = handler.get("namespace")(obj=item).lower().split(".")

      if not handler.get("absolute"):
        final_path = _path + final_path

      #print final_path, item
      
      r = permissions_apply(
        dict_from_namespace(final_path, item), 
        perms_struct, 
        ruleset=rs
      )
      r = dict_get_path(r, final_path)
      if r:
        n.append(r)

    container[0][container[1]] = n



#############################################################################

def permissions_apply(data, perms_struct, path='', debug=False, ruleset=None):
  if not dict_valid(perms_struct):
    load_perms(perms_struct)
    perms_struct = perms_struct._nsp_perms_struct
  rv = permissions_apply_additive(data, perms_struct)

  if debug:
    print json.dumps(rv, indent=2)

  permissions_apply_subtractive(rv, perms_struct)

  if debug:
    print json.dumps(rv, indent=2)

  # apply ruleset
  if ruleset:
    for key, perm in ruleset.get("require", {}).items():
      permissions_apply_ruleset_require_explicit(rv, key, perm, perms_struct)
    for key, hdl in ruleset.get("list-handlers", {}).items():
      permissions_apply_list_handler(rv, key, hdl, perms_struct, ruleset=ruleset)
    
  if debug:
    print json.dumps(rv, indent=2)

  return rv

#############################################################################

def permissions_apply_to_serialized_model(smodel, perms_struct, data=None, ruleset={}):
  if hasattr(smodel, "instance"):
    inst = smodel.instance
  else:
    inst = smodel

  namespace_str = obj_to_namespace(inst)
  namespace = namespace_str.split(".")
  structure = d = {}


  if hasattr(inst, "nsp_ruleset"):
    ruleset.update(inst.nsp_ruleset)

  l = len(namespace)
  i = 0
  while i < l:
    k = namespace[i]
    if i < l-1:
      d[k] = {}
      d = d[k]
    elif data is None:
      d[str(k)] = smodel.data
    else:
      d[str(k)] = data
    i += 1

  
  # prepare ruleset
  if ruleset:
    _ruleset = {}
    for section, rules in ruleset.items():
      _ruleset[section] = {}
      for rule, perms in rules.items():
        _ruleset[section]["%s.%s" % (namespace_str, rule)] = perms
    ruleset = _ruleset

  r = permissions_apply(
    structure,
    perms_struct,
    ruleset=ruleset
  )

  for k in namespace:
    r = r.get(k,{})

  return r

#############################################################################

def perms_structure(perms):
  perms_wc = {"__ps":True}
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
