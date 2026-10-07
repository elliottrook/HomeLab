import unittest
from unittest.mock import Mock
from identity_provision import check_existing_access, provision


class IdentityGuardTests(unittest.TestCase):
    def test_exact_positive_user_only_boundary(self):
        check_existing_access([{'bindings':[dict(user=True,group=False,policy=False,negate=False)]}]*20)

    def test_other_access_shapes_require_review(self):
        for bindings in ([],[dict(user=False,group=True,policy=False,negate=False)],
                [dict(user=True,group=False,policy=False,negate=True)],
                [dict(user=False,group=False,policy=True,negate=False)],
                [dict(user=True,group=False,policy=False,negate=False)]*2):
            with self.subTest(bindings=bindings), self.assertRaises(ValueError):
                check_existing_access([{'bindings':bindings}])

    def test_unapproved_never_imports_django_or_delivers(self):
        deliver=Mock()
        with self.assertRaises(ValueError): provision(deliver)
        deliver.assert_not_called()
