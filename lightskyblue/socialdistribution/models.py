from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    host = models.URLField(default="http://127.0.0.1:8000")

    # keeps track of which authors this author is following (for feed generation and friend checks)
    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        blank=True
    )

    # to get the followers of this author, we can use the reverse relationship "followers" from the following field

    def is_following(self, other_author) -> bool:
        return self.following.filter(id=other_author.id).exists()

    def is_friends_with(self,other_author) -> bool:
        return (
            self.following.filter(id=other_author.id).exists() and
            other_author.following.filter(id=self.id).exists()
        )

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
        ("FRIENDS", "Friends"),
        ("UNLISTED", "Unlisted"),
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
