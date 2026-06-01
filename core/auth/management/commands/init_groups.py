from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.auth.utils.groups import GROUP_PERMISSIONS, create_default_groups


class Command(BaseCommand):
    help = 'Crea los grupos por defecto con sus permisos asignados.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Inicializando grupos por defecto...\n'))

        existing = set(Group.objects.filter(name__in=GROUP_PERMISSIONS.keys())
                       .values_list('name', flat=True))
        create_default_groups()

        for group_name in GROUP_PERMISSIONS:
            if group_name in existing:
                self.stdout.write(self.style.WARNING(f'[OK] Grupo "{group_name}" ya existe'))
            else:
                count = Group.objects.get(name=group_name).permissions.count()
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Grupo "{group_name}" creado con {count} permisos'
                ))

        self.stdout.write(self.style.SUCCESS('\n¡Grupos inicializados correctamente!'))
