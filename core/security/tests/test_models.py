from django.test import TestCase

from core.security.models import Group, Module, ModuleType


class ModuleTests(TestCase):
    def test_to_json_contains_basic_fields(self):
        module_type = ModuleType.objects.create(name="Seguridad", icon="fas fa-shield", order=1)
        module = Module.objects.create(
            module_type=module_type,
            name="Módulos",
            url="/security/module/",
            icon="fas fa-puzzle-piece",
        )
        payload = module.to_json()
        self.assertEqual(payload["name"], "Módulos")
        self.assertEqual(payload["module_type"], "Seguridad")
        self.assertEqual(payload["permissions"], [])


class GroupTests(TestCase):
    def test_str_returns_name(self):
        group = Group.objects.create(name="Administrador")
        self.assertEqual(str(group), "Administrador")
