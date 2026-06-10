from django import forms

from core.security.models import Group


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "description", "is_active"]
