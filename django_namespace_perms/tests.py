from django.test import SimpleTestCase

from django_namespace_perms import util, constants

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
# Create your tests here.

class NSPTestCase(SimpleTestCase):

  perms = {
    "a.b" : constants.PERM_READ,
    "a.b.c" : constants.PERM_READ | constants.PERM_WRITE,
    "a.b.d" : constants.PERM_DENY,
    "b" : constants.PERM_READ
  }
 
  def setUp(self):
    pass

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

  def test_has_perms(self):
    self.assertEqual(util.has_perms(self.perms, "a.b", constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, "a.b", constants.PERM_WRITE), False)
    self.assertEqual(util.has_perms(self.perms, "a.b.c", constants.PERM_WRITE), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.c", constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.d", constants.PERM_READ), False)
    self.assertEqual(util.has_perms(self.perms, "a.b.d", constants.PERM_WRITE), False)

  def test_has_perms_wildcard(self):
    self.assertEqual(util.has_perms(self.perms, "b.*", constants.PERM_READ), True)
    self.assertEqual(util.has_perms(self.perms, "a.b.*", constants.PERM_READ, ambiguous=True), True)
    self.assertEqual(util.has_perms(self.perms, "c.*", constants.PERM_READ, ambiguous=True), False)

  def test_perms_apply(self):
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
    expected = {
      "a" : {
        "b" : {
          "c" : data['a']['b']['c']
        }
      },
      "b" : data['b']
    }

    perms_struct = util.perms_structure(self.perms)
    result = util.permissions_apply(data, perms_struct)
    self.assertEqual(expected, result)

