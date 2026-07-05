from django import forms

from core.scraper.models import ScraperSource


class ScraperSourceForm(forms.ModelForm):
    class Meta:
        model = ScraperSource
        fields = ["name", "url"]
        widgets = {
            "name": forms.TextInput(),
            "url": forms.Textarea(attrs={"rows": 3}),
        }
