import uuid


def validate_password_strength(password):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una mayúscula."
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un dígito."
    return True, ""


def generate_reset_token():
    return str(uuid.uuid4())


def verify_reset_token(token):
    try:
        uuid.UUID(token)
    except (ValueError, AttributeError, TypeError):
        return False
    return True
