from django import forms
from .models import AuthorProfile, Entry
from .models import Comment 

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