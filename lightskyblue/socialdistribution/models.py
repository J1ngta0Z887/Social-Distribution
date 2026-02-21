from django.db import models

class Author(models.Model):
    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="followers",
        blank=True
    )

    def is_following(self, other_author) -> bool:
        return self.following.filter(id=other_author.id).exists()