"""populate_db management command.

When:
- Use in local/dev to seed predictable test users and posts.

How:
- Run: `python manage.py populate_db`

Why/why-not:
- Use for quick demo data and UI testing.
- Do not use in production: inserts fixed sample accounts/content.

Behavior:
- Creates or reuses users: `alice`, `bob`, `charlie`.
- Creates or reuses corresponding `Author` rows.
- Ensures each author has three entries with visibilities:
  `FRIENDS`, `PUBLIC`, `UNLISTED`.
- Uses `get_or_create`, so reruns are mostly idempotent.

Output:
- Success message on completion.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ...models import Author, Entry


class Command(BaseCommand):
    help = 'Populate the database with test authors and entries'

    def handle(self, *args, **options):
        """Seed local test users/authors and starter entries."""
        authors_data = [
            {'username': 'alice', 'display_name': 'Alice Smith', 'bio': 'Tech enthusiast and developer'},
            {'username': 'bob', 'display_name': 'Bob Johnson', 'bio': 'Designer and creative thinker'},
            {'username': 'charlie', 'display_name': 'Charlie Brown', 'bio': 'Data scientist and analyst'},
        ]

        entries_data = [
            {'title': 'First Post', 'content': 'This is my friends post!'},
            {'title': 'Second Post', 'content': 'This is my public post.'},
            {'title': 'Third Post', 'content': 'This is my unlisted post'},
        ]

        for author_info in authors_data:
            # Reuse existing records so reruns don't duplicate core rows.
            user, created = User.objects.get_or_create(
                username=author_info['username'],
                defaults={'first_name': author_info['display_name'].split()[0]}
            )

            author, _ = Author.objects.get_or_create(user=user)

            # Only backfill profile fields when missing.
            if not author.display_name:
                author.display_name = author_info["display_name"]
            if not author.bio:
                author.bio = author_info["bio"]
            author.save()

            visibilities = ['FRIENDS', 'PUBLIC', 'UNLISTED']
            for i, entry_info in enumerate(entries_data, 1):
                Entry.objects.get_or_create(
                    author=author,
                    title=entry_info['title'],
                    defaults={
                        'content': entry_info['content'],
                        'visibility': visibilities[i - 1],
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with test data'))
