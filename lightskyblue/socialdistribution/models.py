from typing import Self
from django.db import models
from django.conf import settings
from django.forms import model_to_dict


class Author(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=80, blank=True)
    host = models.URLField(default="http://127.0.0.1:8000")
    # the max length is arbitrary, just went for size near old tweets max length
    bio = models.TextField(max_length=160, blank=True)
    github_url = models.URLField(blank=True)
    picture_url = models.URLField(blank=True)
    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        blank=True)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["display_name", "host"], name="unique_display_name_host")
        ]

    def update_profile(self, new_data):
        self.display_name = new_data.get("displayName", self.display_name)
        self.bio = new_data.get("bio", self.bio)
        self.github_url = new_data.get("github", self.github_url)
        self.picture_url = new_data.get("profileImage", self.picture_url)
        self.save()

    def is_friends_with(self, other: Self):
        if other is None:
            return False
        # credit: gpt-5.2-codex-low for the really easy pk=other.pk lol
        author_follows_other = self.following.filter(pk=other.pk).exists()
        other_follows_author = other.following.filter(pk=self.pk).exists()

        return author_follows_other and other_follows_author

    def is_following(self, other: Self):
        if other is None:
            return False
        return self.following.filter(pk=other.pk).exists()

    def serialize(self):
        author = {}
        author["type"] = "author"
        author["id"] = f"{self.host}/api/authors/{self.pk}"
        author["host"] = f"{self.host}/api/"
        author["displayName"] = self.display_name
        author["bio"] = self.bio
        author["github"] = self.github_url
        author["profileImage"] = self.picture_url
        author["web"] = f"{self.host}/author/{self.display_name}"
        return author

    def __str__(self):
        return self.display_name or self.user.username


class Entry(models.Model):
    VISIBILITY_CHOICES = [
        ("PUBLIC", "Public"),
        ("FRIENDS", "Friends"),
        ("UNLISTED", "Unlisted"),
        ("FOLLOWERS", "Followers")
    ]

    CONTENT_TYPE_CHOICES = [
        ("text/markdown", "CommonMark"),
        ("text/plain", "Plain Text"),
    ]

    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default="text/plain"
    )

    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="entries")

    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)

    image_url = models.URLField(blank=True)

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="PUBLIC",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    likes = models.ManyToManyField(Author, related_name="liked_entries", blank=True)


    class Meta:
        ordering = ["-created_at"]


    def __str__(self):
        return f"{self.author.user.username}: {self.title or 'Entry'}"

    

class Comment(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    likes = models.ManyToManyField(Author, related_name="liked_comments", blank=True)

    class Meta:
        ordering = ["created_at"]


class ProcessedEvent(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="processed_events")
    event_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['author', 'event_id'], name='unique_author_event')
        ]

class FollowRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
    ]

    from_author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="sent_follow_requests")
    to_author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="received_follow_requests")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    seen_by_target = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_author', 'to_author'], name='unique_follow_request')
        ]
