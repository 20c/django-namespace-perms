from django.test import SimpleTestCase
from django.db import models
from django.conf import settings

from django_namespace_perms import util, constants
import json

###############################################################################
"""
Set TEST_RUNNER to this class in settings for fast testing (no db creation)
"""

from django.test.runner import DiscoverRunner
class NoDbTestRunner(DiscoverRunner):
  def setup_databases(self, **kwargs):
    pass
  def teardown_databases(self, old_config):
    pass

###############################################################################

class ModelTestA(models.Model):
  @property
  def nsp_namespace(self):
    return "test.django_namespace_perms.modeltesta.1"

class ModelTestB(models.Model):
  allowedField = models.CharField(max_length=255)
  deniedField = models.CharField(max_length=255)

class ModelTestC(models.Model):
  @classmethod
  def nsp_namespace_base(cls):
    return "test.django_namespace_perms"

class ModelTestD(ModelTestC):
  @classmethod
  def nsp_namespace_create(cls):
    return "create.test.django_namespace_perms"

###############################################################################
# Create your tests here.

class NSPTestCase(SimpleTestCase):

  perms = {
    "django_namespace_perms.modeltestb.1" : constants.PERM_WRITE,
    "django_namespace_perms.modeltestb.2.allowedfield" : constants.PERM_READ,
    "a.b" : constants.PERM_READ,
    "a.b.c" : constants.PERM_READ | constants.PERM_WRITE,
    "a.b.d" : constants.PERM_DENY,
    "a.100" : constants.PERM_READ,
    "b" : constants.PERM_READ,
    "c.a.$" : constants.PERM_READ,
    "c.a.a" : constants.PERM_READ,

    "e.a" : constants.PERM_READ,
    "e.a.b" : constants.PERM_READ,

    "f.1" : constants.PERM_READ,
    "g.a.1" : constants.PERM_READ,
    "g.b" : constants.PERM_READ,
    "g.c" : constants.PERM_READ,
    "g.c.3" : constants.PERM_READ,

    "h" : constants.PERM_READ,

    "l.o" : constants.PERM_READ,
    "l.o.*.n.*.p.p" : constants.PERM_READ,
    "l.o.1" : constants.PERM_READ | constants.PERM_WRITE,
    "l.o.2" : constants.PERM_READ | constants.PERM_WRITE,

    "x" : constants.PERM_READ,
    "x.c" : constants.PERM_READ,
    "x.*.z" : constants.PERM_READ,
    "x.*.z.c" : constants.PERM_READ,
    "x.y.z.d" : constants.PERM_READ
  }

  perms_crud = {
    "r.a" : constants.PERM_READ,
    "r.a.1" : constants.PERM_UPDATE,
    "r.a.2" : constants.PERM_CREATE,
    "r.a.3" : constants.PERM_DELETE,
    "r.a.4" : constants.PERM_DENY
  }

  def setUp(self):
    settings.NSP_MODE = "rw"

  def test_get_permission_flag_rw_mode(self):
    settings.NSP_MODE = "rw"
    self.assertEqual(util.get_permission_flag("read"), constants.PERM_READ)
    self.assertEqual(util.get_permission_flag("create"), constants.PERM_WRITE)
    self.assertEqual(util.get_permission_flag("add"), constants.PERM_WRITE)
    self.assertEqual(util.get_permission_flag("update"), constants.PERM_WRITE)
    self.assertEqual(util.get_permission_flag("change"), constants.PERM_WRITE)
    self.assertEqual(util.get_permission_flag("delete"), constants.PERM_WRITE)

  def test_get_permission_flag_crud_mode(self):
    settings.NSP_MODE = "crud"
    self.assertEqual(util.get_permission_flag("read"), constants.PERM_READ)
    self.assertEqual(util.get_permission_flag("create"), constants.PERM_CREATE)
    self.assertEqual(util.get_permission_flag("add"), constants.PERM_CREATE)
    self.assertEqual(util.get_permission_flag("update"), constants.PERM_UPDATE)
    self.assertEqual(util.get_permission_flag("change"), constants.PERM_UPDATE)
    self.assertEqual(util.get_permission_flag("delete"), constants.PERM_DELETE)

  def test_namespace_override(self):
    obj = ModelTestA()
    obj.id = 1
    namespace = util.obj_to_namespace(obj)
    self.assertEqual(namespace, "test.django_namespace_perms.modeltesta.1")

  def test_namespace(self):
    obj = ModelTestB()
    obj.id=1
    namespace = util.obj_to_namespace(obj)
    self.assertEqual(namespace, "django_namespace_perms.modeltestb.1")

  def test_namespace_classmethods(self):
    self.assertEqual(util.obj_to_namespace(ModelTestC), "test.django_namespace_perms")
    self.assertEqual(util.obj_to_namespace(ModelTestD), "create.test.django_namespace_perms")

  def test_model_perms(self):
    obj = ModelTestB()
    obj.id = 1
    obj2 = ModelTestB()
    obj2.id = 2
    self.assertEqual(util.has_perms(self.perms, obj, constants.PERM_WRITE), True)
    self.assertEqual(util.has_perms(self.perms, obj2, constants.PERM_WRITE), False)
    self.assertEqual(util.has_perms(self.perms, [obj2, "allowedfield"], constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, [obj2, "deniedfield"], constants.PERM_READ), False)
    self.assertEqual(util.has_perms(self.perms, [obj2, "allowedfield"], constants.PERM_WRITE), False)

  def test_permcode_to_namespace_view(self):
    label, flag = util.permcode_to_namespace("app.view_model")
    self.assertEqual("app.model.view", label)
    self.assertEqual(flag, constants.PERM_READ)

  def test_permcode_to_namespace_add(self):
    label, flag = util.permcode_to_namespace("app.add_model")
    self.assertEqual("app.model.add", label)
    self.assertEqual(flag, constants.PERM_WRITE)

  def test_permcode_to_namespace_delete(self):
    label, flag = util.permcode_to_namespace("app.delete_model")
    self.assertEqual("app.model.delete", label)
    self.assertEqual(flag, constants.PERM_WRITE)

  def test_permcode_to_namespace_change(self):
    label, flag = util.permcode_to_namespace("app.change_model")
    self.assertEqual("app.model.change", label)
    self.assertEqual(flag, constants.PERM_WRITE)

  def test_permcode_to_namespace_view_crud(self):
    settings.NSP_MODE = "crud"
    label, flag = util.permcode_to_namespace("app.view_model")
    self.assertEqual("app.model.view", label)
    self.assertEqual(flag, constants.PERM_READ)

  def test_permcode_to_namespace_add_crud(self):
    settings.NSP_MODE = "crud"
    label, flag = util.permcode_to_namespace("app.add_model")
    self.assertEqual("app.model.add", label)
    self.assertEqual(flag, constants.PERM_CREATE)

  def test_permcode_to_namespace_delete_crud(self):
    settings.NSP_MODE = "crud"
    label, flag = util.permcode_to_namespace("app.delete_model")
    self.assertEqual("app.model.delete", label)
    self.assertEqual(flag, constants.PERM_DELETE)

  def test_permcode_to_namespace_change_crud(self):
    settings.NSP_MODE = "crud"
    label, flag = util.permcode_to_namespace("app.change_model")
    self.assertEqual("app.model.change", label)
    self.assertEqual(flag, constants.PERM_UPDATE)


  def test_has_perms(self):
    self.assertEqual(util.has_perms(self.perms, "a.b", constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, "a.b", constants.PERM_WRITE), False)
    self.assertEqual(util.has_perms(self.perms, "a.b.c", constants.PERM_WRITE), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.c", constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.d", constants.PERM_READ), False)
    self.assertEqual(util.has_perms(self.perms, "a.b.d", constants.PERM_WRITE), False)
   
    self.assertEqual(util.has_perms(self.perms, "e.a.a", constants.PERM_READ, explicit=True), False)
    self.assertEqual(util.has_perms(self.perms, "e.a.b", constants.PERM_READ, explicit=True), True)

    self.assertEqual(util.has_perms(self.perms, "a.b", "read"), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.d", "read"), False)
    self.assertEqual(util.has_perms(self.perms, "a.b.d", "write"), False)
 

  def test_has_perms_crud(self):
    settings.NSP_MODE = "crud"
    self.assertEqual(util.has_perms(self.perms_crud, "r.a", "read"), True)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a", "update"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a", "create"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a", "delete"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.1", "update"), True)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.1", "create"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.1", "delete"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.2", "update"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.2", "create"), True)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.2", "delete"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.3", "update"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.3", "create"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.3", "delete"), True)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.4", "read"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.4", "update"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.4", "create"), False)
    self.assertEqual(util.has_perms(self.perms_crud, "r.a.4", "delete"), False)
    settings.NSP_MODE = "rw"
 

  def test_has_perms_wildcard(self):
    self.assertEqual(util.has_perms(self.perms, "b.*", constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.*", constants.PERM_READ, ambiguous=True), True)
    self.assertEqual(util.has_perms(self.perms, "d\..*", constants.PERM_READ, ambiguous=True), False)

  def test_perms_apply(self):
    data = {
      "a" : {
        "b": {
          "c" : "This should be here",
          "d" : "This should be gone"
        },
        "100" : "This should be here"
      },
      "b" : "This should be here",
      "c" : {
        "a" : {
          "b" : "This should be gone",
          "a" : "This should be here"
        }
      }
    }
    expected = {
      "a" : {
        "100" : data["a"]["100"],
        "b" : {
          "c" : data['a']['b']['c']
        }
      },
      "b" : data['b'],
      "c" : {
        "a" : {
          "a": data['c']['a']['a']
        }
      }
    }

    perms_struct = util.perms_structure(self.perms)
    result = util.permissions_apply(data, perms_struct)
    self.assertEqual(expected, result)

  def test_apply_with_permset(self):
    data = {
      "x" : {
        "a" : "This should be here",
        "b" : "This should be gone",
        "c" : "This should be here",
        "d" : "This should be here",
        "y": {
          "y" : {
            "a" : "This should be here",
            "b" : "This should be gone"
          },
          "z" : {
            "a" : "This should be here",
            "b" : "This should be gone",
            "c" : "This should be here",
            "d" : "This should be here"
          }
        }
      }
    }

    expected = {
      "x" : {
        "a" : data["x"]["a"],
        "c" : data["x"]["c"],
        "d" : data["x"]["d"],
        "y" : {
          "y" : {
            "a" : data["x"]["y"]["y"]["a"]
          },
          "z" : {
            "a" : data["x"]["y"]["z"]["a"],
            "c" : data["x"]["y"]["z"]["c"],
            "d" : data["x"]["y"]["z"]["d"]
          }
        }
      }
    }

    ruleset = {
      "require" : {
        "x.b" : 0x01,
        "x.c" : 0x01,
        "x.y.*.b" : 0x01,
        "x.y.z.c" : 0x01,
        "x.y.z.d" : 0x01
      }
    }

    perms_struct = util.perms_structure(self.perms)
    result = util.permissions_apply(data, perms_struct, debug=False, ruleset=ruleset)
    self.assertEqual(expected, result)

  def test_list_handlers(self):
    
    data = {
      "f" : [
        {"a" : 1, "b" : "should be here" },
        {"a" : 2, "b" : "should be gone" }
      ],
      "g" : {
        "a" : [
          {"a" : 1, "b" : "should be here" },
          {"a" : 2, "b" : "should be gone" }
        ],
        "b" : "should be here",
        "c" : [
          {"a" : 1, "b" : "should be gone" },
          {"a" : 2, "b" : "should be gone" },
          {"a" : 3, "b" : "should be here" }
        ]
      },
      "h" : {
        "a" : [
          {"a" : 1, "b" : "should be here" },
          {"a" : 2, "b" : "should be gone" }
        ],
        "b" : [
          {"a" : 1, "b" : "should be here" },
          {"a" : 2, "b" : "should be gone" }
        ]
      },
      "l": {
        "o": {
          "1" : {
            "n" : {
              "1": {
                "p" : [ "should be here" ],
                "a" : "should be here",
                "b" : "should be here"
              }
            }
          }
        }
      }
    }

    expected = {
      "f" : [
        data["f"][0]
      ],
      "g" : {
        "a" : [
          data["g"]["a"][0]
        ],
        "c" : [
          data["g"]["c"][2]
        ],
        "b" : data["g"]["b"]
      },
      "h" : {
        "a" : [data["h"]["a"][0]],
        "b" : [data["h"]["b"][0]]
      },
      "l": {
        "o": {
          "1" : {
            "n" : {
              "1": {
                "p" : [ "should be here" ],
                "a" : "should be here",
                "b" : "should be here"
              }
            }
          }
        }
      }
 
    }

    def namespace_builder(**kwargs):
      return str(kwargs.get("a"))

    def namespace_builder_absolute(**kwargs):
      return "g.a.%s" % kwargs.get("a")

    def namespace_builder_complex(**kwargs):
      return "p"

    ruleset = {
      "require": {
        "g.c.1" : 0x01,
        "g.c.2" : 0x01,
        "g.c.3" : 0x01,
        "h.*.2" : 0x01,
        "l.o.1.n.p.p" : 0x01
      },
      "list-handlers" : {
        "f" : {
          "namespace" : namespace_builder
        },
        "g.a" : {
          "namespace" : namespace_builder_absolute,
          "absolute" : True
        },
        "g.c" : {
          "namespace" : namespace_builder
        },
        "h.*" : {
          "namespace" : namespace_builder
        },
        "l.o.1.n.1.p" : {
          "namespace" : namespace_builder_complex
        }
      }
    }

    perms_struct = util.perms_structure(self.perms)
    result = util.permissions_apply(data, perms_struct, debug=False, ruleset=ruleset)

    self.assertEqual(expected, result)
    

  def test_performance(self):
    
    def mkdataset(depth=3):
      depth = depth - 1
      if depth <= 0:
        return
      return dict([(str(k),mkdataset(depth=depth)) for k in range(1,1000)])
    data = {
      "a" : mkdataset(3),
      "b" : mkdataset(3)
    }

    ruleset = {
      "require" : {
        "a.100.100" : 0x01,
      }
    }

    ruleset["require"].update(**dict([("b.100.%d" % i, 0x01) for i in range(1,100)]))

    import time
    
    perms_struct = util.perms_structure(self.perms)
    
    t= time.time()
    result = util.permissions_apply(data, perms_struct, debug=False)
    diff = time.time() - t
    print "\n\nPerformance test took: %.5f seconds" % (diff)
    
    t = time.time()
    result = util.permissions_apply(data, perms_struct, debug=False, ruleset=ruleset)
    diff = time.time() - t
    print "\n\nPerformance (w/ Explicit ruleset) test took: %.5f seconds" % (diff)

