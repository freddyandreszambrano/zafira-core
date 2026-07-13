from django.core.management import call_command
from django.test import TestCase

from core.auth.models import User
from core.security.management.commands.insert_data import MODULE_TYPES, MODULES
from core.security.models import Group, GroupModule, Module, ModuleType


class SeedProductionDataCommandTests(TestCase):
    def test_creates_menu_and_administrator_group_without_creating_users(self):
        call_command("seed_production_data")

        group = Group.objects.get(name="Administrador")
        self.assertEqual(ModuleType.objects.count(), len(MODULE_TYPES))
        self.assertEqual(Module.objects.count(), len(MODULES))
        self.assertEqual(GroupModule.objects.filter(group=group).count(), len(MODULES))
        self.assertFalse(User.objects.exists())

    def test_is_idempotent(self):
        call_command("seed_production_data")
        call_command("seed_production_data")

        self.assertEqual(ModuleType.objects.count(), len(MODULE_TYPES))
        self.assertEqual(Module.objects.count(), len(MODULES))
        self.assertEqual(Group.objects.count(), 1)
