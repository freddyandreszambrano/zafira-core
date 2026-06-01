from django import forms
from django.contrib.auth import authenticate

from core.auth.models import User
from core.common.constants import (
    MSG_INACTIVE_ACCOUNT,
    MSG_INVALID_CREDENTIALS,
    MSG_PASSWORDS_MISMATCH,
)
from core.common.forms.widgets import email_input, password_input, text_input


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=text_input('Usuario', extra_attrs={'autocomplete': 'username'}),
    )
    password = forms.CharField(widget=password_input('Contraseña'))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError(MSG_INVALID_CREDENTIALS)
            if not self.user.is_active:
                raise forms.ValidationError(MSG_INACTIVE_ACCOUNT)
        return self.cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=password_input('Contraseña', autocomplete='new-password'))
    password_confirm = forms.CharField(
        widget=password_input('Confirmar contraseña', autocomplete='new-password'),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'dni', 'first_name', 'last_name']
        widgets = {
            'username': text_input('Usuario'),
            'email': email_input('Correo'),
            'dni': text_input('Cédula'),
            'first_name': text_input('Nombres'),
            'last_name': text_input('Apellidos'),
        }

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(MSG_PASSWORDS_MISMATCH)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
