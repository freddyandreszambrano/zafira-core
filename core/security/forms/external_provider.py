import secrets

from django import forms

from core.common.forms.widgets import checkbox_input, text_input
from core.security.models import ExternalProvider


class ExternalProviderForm(forms.ModelForm):
    class Meta:
        model = ExternalProvider
        fields = ["name", "client_secret", "is_active"]
        widgets = {
            "name": text_input("Nombre del servicio externo"),
            "client_secret": text_input(
                "Dejar vacío para autogenerar",
                extra_attrs={"autocomplete": "off", "spellcheck": "false"},
            ),
            "is_active": checkbox_input(),
        }
        help_texts = {
            "client_secret": (
                "Secreto compartido para firmar HMAC. "
                "Si lo dejas vacío se genera uno seguro automáticamente."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client_secret"].required = False

    def clean_client_secret(self):
        value = (self.cleaned_data.get("client_secret") or "").strip()
        return value or secrets.token_urlsafe(32)
