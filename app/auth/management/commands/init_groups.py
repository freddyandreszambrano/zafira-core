"""Management command to initialize default groups and permissions."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from app.auth.models import User


class Command(BaseCommand):
    """Initialize default user groups with permissions."""

    help = 'Create default user groups with appropriate permissions'

    def handle(self, *args, **options):
        """Handle command execution."""
        self.stdout.write(self.style.SUCCESS('Inicializando grupos por defecto...\n'))

        # Define groups and their permissions
        groups_config = {
            'Admin': [
                'add_user', 'change_user', 'delete_user', 'view_user',
                'add_group', 'change_group', 'delete_group', 'view_group',
                'add_permission', 'change_permission', 'delete_permission', 'view_permission',
            ],
            'Manager': [
                'view_user', 'add_user', 'change_user',
                'view_group', 'view_permission',
            ],
            'User': [
                'view_user',
            ],
        }

        content_type = ContentType.objects.get_for_model(User)

        for group_name, permissions in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                # Get permissions
                perms = Permission.objects.filter(
                    content_type=content_type,
                    codename__in=permissions
                )
                group.permissions.set(perms)
                msg = self.style.SUCCESS(
                    f'[OK] Grupo "{group_name}" creado con {perms.count()} permisos'
                )
            else:
                msg = self.style.WARNING(
                    f'[OK] Grupo "{group_name}" ya existe'
                )

            self.stdout.write(msg)

        self.stdout.write(
            self.style.SUCCESS('\n¡Grupos inicializados correctamente!')
        )
