from django.test import TestCase

from core.auth.utils.validators import (
    generate_reset_token,
    validate_password_strength,
    verify_reset_token,
)


class ValidatorsTests(TestCase):
    def test_password_too_short(self):
        ok, _ = validate_password_strength('Aa1')
        self.assertFalse(ok)

    def test_password_without_uppercase(self):
        ok, _ = validate_password_strength('abcdef1234')
        self.assertFalse(ok)

    def test_password_without_digit(self):
        ok, _ = validate_password_strength('Abcdefghij')
        self.assertFalse(ok)

    def test_password_valid(self):
        ok, msg = validate_password_strength('Abcdef1234')
        self.assertTrue(ok)
        self.assertEqual(msg, '')

    def test_reset_token_roundtrip(self):
        token = generate_reset_token()
        self.assertTrue(verify_reset_token(token))

    def test_reset_token_invalid(self):
        self.assertFalse(verify_reset_token('not-a-uuid'))
        self.assertFalse(verify_reset_token(None))


class EmailUtilsTests(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)


class GroupsUtilsTests(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)
