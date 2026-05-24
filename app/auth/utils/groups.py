from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


GROUP_PERMISSIONS = {
    'Admin': [
        'add_user', 'change_user', 'delete_user', 'view_user',
        'add_group', 'change_group', 'delete_group', 'view_group',
        'add_permission', 'change_permission', 'delete_permission', 'view_permission',
    ],
    'Manager': [
        'view_user', 'add_user', 'change_user',
        'view_group', 'view_permission',
    ],
    'User': ['view_user'],
}


def create_default_groups():
    from app.auth.models import User

    content_type = ContentType.objects.get_for_model(User)
    for group_name, codenames in GROUP_PERMISSIONS.items():
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            perms = Permission.objects.filter(
                content_type=content_type, codename__in=codenames,
            )
            group.permissions.set(perms)


def assign_user_to_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        raise ValueError(f'Grupo "{group_name}" no existe. Crea los grupos primero.')
    user.groups.add(group)
    return group


def remove_user_from_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        raise ValueError(f'Grupo "{group_name}" no existe.')
    user.groups.remove(group)
    return group
