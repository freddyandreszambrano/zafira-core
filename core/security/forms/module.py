from django import forms

from core.security.models import Module, ModuleType


class ModuleTypeForm(forms.ModelForm):
    class Meta:
        model = ModuleType
        fields = ["name", "icon", "description", "order", "is_active"]


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = [
            "module_type",
            "name",
            "url",
            "icon",
            "description",
            "order",
            "is_active",
            "is_visible",
            "is_vertical",
            "permits",
        ]
