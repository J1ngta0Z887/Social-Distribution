from django import forms
from .models import AuthorProfile, Entry

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = AuthorProfile
        fields = ["display_name", "bio", "picture_url", "github_url"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ["title", "content", "image_url", "visibility"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }