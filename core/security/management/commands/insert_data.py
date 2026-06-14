import random
import string

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from rest_framework.authtoken.models import Token

from core.auth.models import User
from core.security.models import Group, GroupModule, GroupPermission, Module, ModuleType
from core.utils.enums import UserTypeChoices

MODULE_TYPES = [
    {"name": "Seguridad", "icon": "fas fa-shield-alt", "order": 1},
    {"name": "Usuarios", "icon": "fas fa-users", "order": 2},
    {"name": "Cuenta", "icon": "fas fa-user-circle", "order": 3},
    {"name": "Herramientas", "icon": "fas fa-toolbox", "order": 4},
]

MODULES = [
    {
        "type": "Seguridad",
        "name": "Módulos",
        "url": "/security/module/",
        "icon": "fas fa-puzzle-piece",
        "description": "Gestión de módulos del sistema",
        "permits_app": "security",
        "permits_model": "module",
        "order": 1,
    },
    {
        "type": "Seguridad",
        "name": "Tipos de módulo",
        "url": "/security/module_type/",
        "icon": "fas fa-layer-group",
        "description": "Categorías para agrupar módulos",
        "permits_app": "security",
        "permits_model": "moduletype",
        "order": 2,
    },
    {
        "type": "Seguridad",
        "name": "Grupos",
        "url": "/security/group/",
        "icon": "fas fa-user-tag",
        "description": "Grupos de seguridad y permisos asignados",
        "permits_app": "security",
        "permits_model": "group",
        "order": 3,
    },
    {
        "type": "Seguridad",
        "name": "Proveedores externos",
        "url": "/security/external_provider/",
        "icon": "fas fa-plug",
        "description": "Credenciales HMAC de servicios externos",
        "permits_app": "security",
        "permits_model": "externalprovider",
        "order": 4,
    },
    {
        "type": "Usuarios",
        "name": "Usuarios",
        "url": "/user/",
        "icon": "fas fa-users",
        "description": "Listado y administración de usuarios",
        "permits_app": "users",
        "permits_model": "user",
        "order": 1,
    },
    {
        "type": "Usuarios",
        "name": "Perfiles mobile",
        "url": "/mobile-profile/",
        "icon": "fas fa-mobile-screen-button",
        "description": "Consulta de perfiles mobile registrados desde la app",
        "permits_app": "profiles",
        "permits_model": "mobileprofile",
        "order": 2,
    },
    {
        "type": "Cuenta",
        "name": "Mi perfil",
        "url": "/profile/",
        "icon": "fas fa-user",
        "description": "Información de la cuenta del usuario",
        "permits_app": None,
        "permits_model": None,
        "order": 1,
        "is_visible": False,
    },
    {
        "type": "Cuenta",
        "name": "Cambiar contraseña",
        "url": "/profile/password/",
        "icon": "fas fa-key",
        "description": "Permite cambiar la contraseña de tu cuenta",
        "permits_app": None,
        "permits_model": None,
        "order": 2,
        "is_visible": False,
    },
    {
        "type": "Herramientas",
        "name": "Scraper",
        "url": "/scraper/",
        "icon": "fas fa-magnifying-glass-chart",
        "description": "Extractor temporal de productos desde tiendas web",
        "permits_app": None,
        "permits_model": None,
        "order": 1,
    },
]


class Command(BaseCommand):
    help = "Inserta tipos de módulo, módulos, grupos y usuario administrador por defecto."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("===== INICIALIZANDO DATOS DE SEGURIDAD =====\n"))

        types = {}
        for cfg in MODULE_TYPES:
            mt, created = ModuleType.objects.update_or_create(
                name=cfg["name"],
                defaults={"icon": cfg["icon"], "order": cfg["order"], "is_active": True},
            )
            types[cfg["name"]] = mt
            self._print_status(f"ModuleType {mt.name}", created)

        modules = []
        for cfg in MODULES:
            module, created = Module.objects.update_or_create(
                url=cfg["url"],
                defaults={
                    "module_type": types.get(cfg["type"]),
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
                ct = ContentType.objects.filter(
                    app_label=cfg["permits_app"],
                    model=cfg["permits_model"],
                ).first()
                if ct:
                    perms = Permission.objects.filter(content_type=ct)
                    module.permits.set(perms)
            modules.append(module)
            self._print_status(f"Module {module.name}", created)

        group, created = Group.objects.get_or_create(
            name="Administrador",
            defaults={"description": "Grupo con acceso total al sistema.", "is_active": True},
        )
        self._print_status(f"Group {group.name}", created)

        for module in modules:
            GroupModule.objects.get_or_create(group=group, module=module)
            for perm in module.permits.all():
                GroupPermission.objects.get_or_create(
                    group=group,
                    module=module,
                    permission=perm,
                )

        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Administrador",
                "last_name": "ZAFIRA",
                "email": "admin@zafira.local",
                "is_active": True,
                "is_superuser": True,
                "is_staff": True,
                "user_type": UserTypeChoices.ADMIN,
                "dni": "".join(random.choices(string.digits, k=10)),
            },
        )
        if user.user_type != UserTypeChoices.ADMIN:
            user.user_type = UserTypeChoices.ADMIN
            user.save(update_fields=["user_type"])
        if created:
            user.set_password("admin")
            user.save()
        user.security_groups.add(group)
        self._print_status(f"User {user.username}", created)

        token, _ = Token.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(f"\nToken para pruebas API: Token {token.key}"))
        self.stdout.write(self.style.SUCCESS("\n¡Datos iniciales cargados correctamente!"))

    def _print_status(self, label, created):
        style = self.style.SUCCESS if created else self.style.WARNING
        prefix = "creado" if created else "ya existe"
        self.stdout.write(style(f"  [{prefix}] {label}"))
