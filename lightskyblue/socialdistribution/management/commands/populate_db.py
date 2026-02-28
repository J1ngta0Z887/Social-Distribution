from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from socialdistribution.models import Author, Entry


class Command(BaseCommand):
    help = 'Populate the database with test authors and entries'

    def handle(self, *args, **options):
        # Create 3 users and authors
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
            # Create or get user
            user, created = User.objects.get_or_create(
                username=author_info['username'],
                defaults={'first_name': author_info['display_name'].split()[0]}
            )

            # Create or get author
            author, _ = Author.objects.get_or_create(user=user)

            # Fill in author details
            if not author.display_name:
                author.display_name = author_info["display_name"]
            if not author.bio:
                author.bio = author_info["bio"]
            author.save()

            # Create 3 entries for this author
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
