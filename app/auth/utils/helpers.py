"""Utility functions for authentication module."""

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app.auth.models import User


def send_password_reset_email(email, user_name, reset_link):
    """
    Send password reset email to user.

    Args:
        email: User email
        user_name: User full name
        reset_link: Password reset link
    """
    subject = 'Resetea tu contraseña - ZAFIRA'
    message = f'''
    Hola {user_name},

    Hemos recibido una solicitud para resetear tu contraseña.
    Haz clic en el siguiente enlace para continuar:

    {reset_link}

    Si no realizaste esta solicitud, puedes ignorar este mensaje.

    Saludos,
    El equipo de ZAFIRA
    '''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_welcome_email(email, user_name, temporary_password=None):
    """
    Send welcome email to new user.

    Args:
        email: User email
        user_name: User full name
        temporary_password: Optional temporary password
    """
    subject = 'Bienvenido a ZAFIRA'
    message = f'''
    Hola {user_name},

    Tu cuenta en ZAFIRA ha sido creada exitosamente.

    Usuario: {email}
    {f'Contraseña temporal: {temporary_password}' if temporary_password else ''}

    Para acceder, visita: {settings.FRONTEND_URL}

    Saludos,
    El equipo de ZAFIRA
    '''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def validate_password_strength(password):
    """
    Validate password strength.
    
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una mayúscula."
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un dígito."
    return True, ""


def generate_reset_token():
    """Generate a unique password reset token."""
    import uuid
    return str(uuid.uuid4())


def verify_reset_token(token):
    """Verify if reset token is valid."""
    # This would typically check against database
    # For now, just verify it's a valid UUID
    try:
        import uuid
        uuid.UUID(token)
        return True
    except ValueError:
        return False


def create_default_groups():
    """Create default user groups with basic permissions."""
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
            print(f'✓ Grupo "{group_name}" creado con {perms.count()} permisos')
        else:
            print(f'✓ Grupo "{group_name}" ya existe')


def assign_user_to_group(user, group_name):
    """
    Assign user to a group.

    Args:
        user: User instance
        group_name: Name of the group

    Returns:
        Group instance
    """
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return group
    except Group.DoesNotExist:
        raise ValueError(f'Grupo "{group_name}" no existe. Crea los grupos primero.')


def remove_user_from_group(user, group_name):
    """
    Remove user from a group.

    Args:
        user: User instance
        group_name: Name of the group

    Returns:
        Group instance
    """
    try:
        group = Group.objects.get(name=group_name)
        user.groups.remove(group)
        return group
    except Group.DoesNotExist:
        raise ValueError(f'Grupo "{group_name}" no existe.')
