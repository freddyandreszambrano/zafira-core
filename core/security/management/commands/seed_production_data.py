from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from core.security.management.commands.insert_data import MODULE_TYPES, MODULES
from core.security.models import Group, GroupModule, GroupPermission, Module, ModuleType


class Command(BaseCommand):
    help = "Carga el menú y grupo iniciales sin crear usuarios ni tokens."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("===== CARGANDO DATOS DE PRODUCCION =====\n"))

        types = {}
        for cfg in MODULE_TYPES:
            module_type, created = ModuleType.objects.update_or_create(
                name=cfg["name"],
                defaults={"icon": cfg["icon"], "order": cfg["order"], "is_active": True},
            )
            types[cfg["name"]] = module_type
            self._print_status(f"ModuleType {module_type.name}", created)

        modules = []
        for cfg in MODULES:
            module, created = Module.objects.update_or_create(
                url=cfg["url"],
                defaults={
                    "module_type": types[cfg["type"]],
                    "name": cfg["name"],
                    "icon": cfg["icon"],
                    "description": cfg["description"],
                    "order": cfg.get("order", 0),
                    "is_active": True,
                    "is_visible": cfg.get("is_visible", True),
                    "is_vertical": cfg.get("is_vertical", False),
                },
            )
            if cfg.get("permits_app") and cfg.get("permits_model"):
                content_type = ContentType.objects.filter(
                    app_label=cfg["permits_app"],
                    model=cfg["permits_model"],
                ).first()
                if content_type:
                    module.permits.set(Permission.objects.filter(content_type=content_type))
            modules.append(module)
            self._print_status(f"Module {module.name}", created)

        group, created = Group.objects.get_or_create(
            name="Administrador",
            defaults={"description": "Grupo con acceso total al sistema.", "is_active": True},
        )
        self._print_status(f"Group {group.name}", created)

        for module in modules:
            GroupModule.objects.get_or_create(group=group, module=module)
            for permission in module.permits.all():
                GroupPermission.objects.get_or_create(
                    group=group,
                    module=module,
                    permission=permission,
                )

        self.stdout.write(self.style.SUCCESS("\nDatos de producción cargados correctamente."))

    def _print_status(self, label, created):
        style = self.style.SUCCESS if created else self.style.WARNING
        prefix = "creado" if created else "ya existe"
        self.stdout.write(style(f"  [{prefix}] {label}"))
