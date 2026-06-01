from django import forms

from core.auth.models import User
from core.common.forms.widgets import checkbox_input, email_input, file_input, text_input


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'image']
        widgets = {
            'first_name': text_input(),
            'last_name': text_input(),
            'email': email_input(),
            'image': file_input(),
        }


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'dni', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'username': text_input(),
            'email': email_input(),
            'dni': text_input(),
            'first_name': text_input(),
            'last_name': text_input(),
            'is_active': checkbox_input(),
            'is_staff': checkbox_input(),
        }
