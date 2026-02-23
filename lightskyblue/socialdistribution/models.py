from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    host = models.URLField(default="http://127.0.0.1:8000")

    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        blank=True
    )

    def is_following(self, other_author) -> bool:
        return self.following.filter(id=other_author.id).exists()
    

class AuthorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)
    github_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    picture_url = models.URLField(blank=True)

    def __str__(self):
        return self.display_name or self.user.username
    

class Entry(models.Model):
    VISIBILITY_CHOICES = [
        ("PUBLIC", "Public"),
        ("LOCAL", "Local"),
        ("FRIENDS", "Friends"),
        ("UNLISTED", "Unlisted"),
    ]

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="entries")

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)

    image_url = models.URLField(blank=True)

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="LOCAL",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author.user.username}: {self.title or 'Entry'}"