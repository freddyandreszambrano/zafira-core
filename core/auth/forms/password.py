from django import forms

from core.common.constants import MSG_PASSWORDS_MISMATCH
from core.common.forms.widgets import password_input


def _validate_match(password, confirm, message=MSG_PASSWORDS_MISMATCH):
    if password and confirm and password != confirm:
        raise forms.ValidationError(message)


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=password_input('Contraseña actual'))
    new_password = forms.CharField(
        widget=password_input('Nueva contraseña', autocomplete='new-password'),
    )
    new_password_confirm = forms.CharField(
        widget=password_input('Confirmar contraseña', autocomplete='new-password'),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        old_password = cleaned.get('old_password')
        if old_password and not self.user.check_password(old_password):
            raise forms.ValidationError('La contraseña actual es incorrecta.')
        _validate_match(
            cleaned.get('new_password'),
            cleaned.get('new_password_confirm'),
            'Las nuevas contraseñas no coinciden.',
        )
        return cleaned


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=password_input('Nueva contraseña', autocomplete='new-password'),
    )
    new_password_confirm = forms.CharField(
        widget=password_input('Confirmar contraseña', autocomplete='new-password'),
    )

    def clean(self):
        cleaned = super().clean()
        _validate_match(cleaned.get('new_password'), cleaned.get('new_password_confirm'))
        return cleaned
