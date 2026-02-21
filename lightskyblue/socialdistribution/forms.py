from django import forms
from .models import AuthorProfile

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = AuthorProfile
        fields = ["display_name", "bio", "picture_url", "github_url"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }