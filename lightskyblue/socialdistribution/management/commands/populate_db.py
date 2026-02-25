from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from socialdistribution.models import Author, AuthorProfile, Entry


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
            {'title': 'First Post', 'content': 'This is my first post on the platform!'},
            {'title': 'Second Post', 'content': 'Sharing my thoughts on technology and design.'},
            {'title': 'Third Post', 'content': 'Check out this interesting development I discovered.'},
        ]

        for author_info in authors_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                username=author_info['username'],
                defaults={'first_name': author_info['display_name'].split()[0]}
            )

            # Create or get author
            author, _ = Author.objects.get_or_create(user=user)

            # Create or get profile
            profile, _ = AuthorProfile.objects.get_or_create(
                user=user,
                defaults={'display_name': author_info['display_name'], 'bio': author_info['bio']}
            )

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
