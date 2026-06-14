from django.test import SimpleTestCase

from core.utils.enums import BaseTextChoices, DepartmentChoices


class DemoChoices(BaseTextChoices):
    ALPHA = "a", "Alpha"
    BETA = "b", "Beta"


class TextChoicesCustomTests(SimpleTestCase):
    def test_get_value_returns_db_value_from_label(self):
        self.assertEqual(DemoChoices.get_value("Alpha"), "a")

    def test_get_value_unknown_label_returns_empty(self):
        self.assertEqual(DemoChoices.get_value("Unknown"), "")

    def test_get_label_returns_label_from_value(self):
        self.assertEqual(DemoChoices.get_label("b"), "Beta")

    def test_get_label_unknown_value_returns_empty(self):
        self.assertEqual(DemoChoices.get_label("zzz"), "")

    def test_get_value_by_label_strips_whitespace(self):
        self.assertEqual(DemoChoices.get_value_by_label("  Alpha  "), "a")

    def test_get_value_by_label_none_safe(self):
        self.assertEqual(DemoChoices.get_value_by_label(None), "")


class DepartmentTests(SimpleTestCase):
    def test_choices_present(self):
        values = {value for value, _ in DepartmentChoices.choices}
        self.assertIn("rrhh", values)
        self.assertIn("otro", values)

    def test_default_label_in_spanish(self):
        self.assertEqual(DepartmentChoices.get_label("rrhh"), "RECURSOS HUMANOS")
