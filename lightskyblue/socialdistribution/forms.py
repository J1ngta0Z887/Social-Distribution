from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
from .models import Author, Entry, Comment

User = get_user_model()

class SignupForm(UserCreationForm):
    display_name = forms.CharField(max_length=80, required=False, label="Display Name")
    bio = forms.CharField(max_length=160, required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Bio")
    picture_url = forms.URLField(required=False, label="Profile Picture URL")
    github_url = forms.CharField(required=False, label="GitHub URL")

    class Meta:
        model = User
        fields = ("username", "password1", "password2", "display_name", "bio", "picture_url", "github_url")

    def clean_display_name(self):
        display_name = self.cleaned_data.get("display_name", "").strip()
        if not display_name:
            return display_name
        
        # Check if this display_name is already taken on the default host
        default_host = "http://127.0.0.1:8000"
        if Author.objects.filter(display_name=display_name, host=default_host).exists():
            raise forms.ValidationError(
                f"The display name '{display_name}' is already taken on this server. "
                "Please choose a different display name, or leave it blank to use your username."
            )
        
        return display_name

    def clean_github_url(self):
        url = (self.cleaned_data.get("github_url") or "").strip()
        if not url:
            return url

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            URLValidator()(url)
        except ValidationError:
            raise forms.ValidationError("Enter a valid URL.")

        parsed = urlparse(url)
        if parsed.netloc not in ["github.com", "www.github.com"]:
            raise forms.ValidationError("Enter a valid GitHub URL (github.com/username).")

        return url

    def save(self, commit=True):
        user = super().save(commit)
        Author.objects.create(
            user=user,
            display_name=self.cleaned_data.get("display_name") or user.username,
            bio=self.cleaned_data.get("bio", ""),
            picture_url=self.cleaned_data.get("picture_url", ""),
            github_url=self.cleaned_data.get("github_url", "")
        )
        return user


class AuthorForm(forms.ModelForm):
    # override model URLField with a CharField
    github_url = forms.CharField(required=False)

    class Meta:
        model = Author
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

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 2, "placeholder": "Write a comment..."})
        }
