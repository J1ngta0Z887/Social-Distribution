from django import forms
from .models import AuthorProfile, Entry
from urllib.parse import urlparse

from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
from .models import AuthorProfile

class AuthorProfileForm(forms.ModelForm):
    # override model URLField with a CharField
    github_url = forms.CharField(required=False)

    class Meta:
        model = AuthorProfile
        fields = ["display_name", "bio", "picture_url", "github_url"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

    def clean_github_url(self):
        url = (self.cleaned_data.get("github_url") or "").strip()
        if not url:
            return url

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # now validate it's a real URL
        try:
            URLValidator()(url)
        except ValidationError:
            raise forms.ValidationError("Enter a valid URL.")

        parsed = urlparse(url)
        if parsed.netloc not in ["github.com", "www.github.com"]:
            raise forms.ValidationError("Enter a valid GitHub URL (github.com/username).")

        return url

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ["title", "content", "image_url", "visibility", "content_type"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4}),
        }