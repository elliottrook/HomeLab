"""Dependency-free tests for the approval ingress passkey mapping."""

import unittest

from approval_passkey_config import PASSKEY_ACR, passkey_acrs


class ApprovalPasskeyConfigTests(unittest.TestCase):
    def test_missing_or_blank_configuration_preserves_yellow_only_mode(self):
        for value in (None, "", "   "):
            with self.subTest(value=value):
                self.assertEqual(frozenset(), passkey_acrs(value))

    def test_exact_reviewed_webauthn_acr_is_the_only_enabled_mapping(self):
        self.assertEqual(frozenset({PASSKEY_ACR}), passkey_acrs(PASSKEY_ACR))
        self.assertEqual(frozenset({PASSKEY_ACR}), passkey_acrs(f"  {PASSKEY_ACR}  "))

    def test_generic_alternate_or_multiple_values_fail_closed(self):
        for value in (
            "mfa",
            "webauthn",
            "urn:example:webauthn",
            PASSKEY_ACR + ",mfa",
            PASSKEY_ACR + "," + PASSKEY_ACR,
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    passkey_acrs(value)


if __name__ == "__main__":
    unittest.main()
