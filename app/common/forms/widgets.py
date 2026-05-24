from django import forms

from app.common.constants import FORM_CHECKBOX_CLASS, FORM_INPUT_CLASS


def text_input(placeholder='', extra_attrs=None):
    attrs = {'class': FORM_INPUT_CLASS, 'placeholder': placeholder}
    if extra_attrs:
        attrs.update(extra_attrs)
    return forms.TextInput(attrs=attrs)


def email_input(placeholder='', extra_attrs=None):
    attrs = {'class': FORM_INPUT_CLASS, 'placeholder': placeholder}
    if extra_attrs:
        attrs.update(extra_attrs)
    return forms.EmailInput(attrs=attrs)


def password_input(placeholder='', autocomplete='current-password'):
    return forms.PasswordInput(attrs={
        'class': FORM_INPUT_CLASS,
        'placeholder': placeholder,
        'autocomplete': autocomplete,
    })


def file_input(accept='image/*'):
    return forms.FileInput(attrs={'class': FORM_INPUT_CLASS, 'accept': accept})


def checkbox_input():
    return forms.CheckboxInput(attrs={'class': FORM_CHECKBOX_CLASS})
