from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Author


# note: test cases were generated with codex and then checked
# by Chris; if there's some weird issue, please let me know
class AuthorAPITest(TestCase):
    new_payload = {
        "displayName": "New Author",
        "bio": "A new author.",
        "github": "https://github.com/new",
        "profileImage": "http://example.com/new.jpg",
    }
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="a",
            password="aaaabbbb",
        )
        self.author = Author.objects.create(
            user=self.user,
            display_name="Author One",
            host="http://testserver",
            bio="A test author.",
            github_url="https://github.com/example",
            picture_url="http://example.com/pic.jpg",
        )

    def tearDown(self):
        self.author.delete()
        self.user.delete()

    def test_get_author_returns_serialized_payload(self):
        response = self.client.get(f"/api/authors/{self.author.id}")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "author")
        self.assertEqual(payload["displayName"], "Author One")
        self.assertEqual(payload["bio"], "A test author.")
        self.assertEqual(payload["github"], "https://github.com/example")
        self.assertEqual(payload["profileImage"], "http://example.com/pic.jpg")
        self.assertEqual(payload["id"], f"http://testserver/api/authors/{self.author.id}")

    def test_missing_author_returns_empty_object(self):
        response = self.client.get("/api/authors/999999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_put_author_logged_out_returns_401(self):
        response = self.client.put(
            f"/api/authors/{self.author.id}",
            data = self.new_payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {})

    def test_put_author_logged_in_updates_profile(self):
        self.client.force_login(self.user)

        response = self.client.put(
            f"/api/authors/{self.author.id}",
            data = self.new_payload,
            content_type = "application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["displayName"], "New Author")
        self.assertEqual(payload["bio"], "A new author.")
        self.assertEqual(payload["github"], "https://github.com/new")
        self.assertEqual(payload["profileImage"], "http://example.com/new.jpg")

        self.author.refresh_from_db()
        self.assertEqual(self.author.display_name, "New Author")
        self.assertEqual(self.author.bio, "A new author.")
        self.assertEqual(self.author.github_url, "https://github.com/new")
        self.assertEqual(self.author.picture_url, "http://example.com/new.jpg")

    def test_get_following_returns_followed_authors(self):
        total_authors = 5
        for i in range(total_authors):
            other_user = get_user_model().objects.create_user(
                username=f"b{i}",
                password=f"bbbbcccc{i}",
            )
            other_author = Author.objects.create(
                user=other_user,
                display_name=f"Author{i}",
                host=f"http://testserver/{i}",
            )
            self.addCleanup(other_author.delete)
            self.addCleanup(other_user.delete)

            self.author.following.add(other_author)

        response = self.client.get(f"/api/authors/{self.author.id}/following")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "authors")
        self.assertEqual(len(payload["authors"]), total_authors)

    def test_get_following_empty_list(self):
        response = self.client.get(f"/api/authors/{self.author.id}/following")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "authors")
        self.assertEqual(payload["authors"], [])
