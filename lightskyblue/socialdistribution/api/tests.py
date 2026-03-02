from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Author, FollowRequest


# note: test cases were generated with codex and then checked
# by Chris; if there's some weird issue, please let me know
class AuthorAPITest(TestCase):
    user_model = get_user_model()
    new_payload = {
        "displayName": "New Author",
        "bio": "A new author.",
        "github": "https://github.com/new",
        "profileImage": "http://example.com/new.jpg",
    }
    def setUp(self):
        self.user = self.user_model.objects.create_user(
            username="user",
            password="secretpassword",
        )
        self.author = Author.objects.create(
            user=self.user,
            display_name="Author One",
            host="http://testserver",
            bio="A test author.",
            github_url="https://github.com/example",
            picture_url="http://example.com/pic.jpg",
        )
        self.client.force_login(self.user)

        self.other_user = self.user_model.objects.create_user(
            username="user2",
            password="secretpassword2",
        )
        self.other_author = Author.objects.create(
            user=self.other_user,
            display_name="Author Two",
            host="http://testserver",
            bio="A second test author.",
            github_url="https://github.com/example",
            picture_url="http://example.com/pic.jpg"
        )

    def tearDown(self):
        self.author.delete()
        self.user.delete()
        self.other_author.delete()
        self.other_user.delete()

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
        response = self.client.get("/api/authors/9999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {})

    def test_put_author_logged_out_returns_401(self):
        self.client.logout()
        response = self.client.put(
            f"/api/authors/{self.author.id}",
            data = self.new_payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {})
        self.client.force_login(self.user)

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

    def test_get_following_returns_followed_authors_and_get_followers_returns_following_authors(self):
        total_authors = 5
        other_authors = []
        for i in range(total_authors):
            other_user = self.user_model.objects.create_user(
                username=f"b{i}",
                password=f"bbbbcccc{i}",
            )
            other_authors.append(Author.objects.create(
                user=other_user,
                display_name=f"Author{i}",
                host=f"http://testserver/{i}",
            ))
            self.addCleanup(other_authors[i].delete)
            self.addCleanup(other_user.delete)

            self.author.following.add(other_authors[i])


        # testing the following api
        response = self.client.get(f"/api/authors/{self.author.id}/following")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "following")
        self.assertEqual(len(payload["authors"]), total_authors)

        # testing the followers api
        for other_author in other_authors:
            response = self.client.get(f"/api/authors/{other_author.id}/followers")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["type"], "followers")
            # only the top-level `author` should be in here
            self.assertDictEqual(payload["authors"][0], self.author.serialize())

    def test_get_following_empty_list(self):
        response = self.client.get(f"/api/authors/{self.author.id}/following")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "following")
        self.assertEqual(payload["authors"], [])

    def test_follow_request_api(self):
        # first we test usage with follows pending
        other_user = self.user_model.objects.create_user(
            username="follower",
            password="passpass",
        )
        other_author = Author.objects.create(
            user=other_user,
            display_name="Follower",
            host="http://testserver",
        )
        self.addCleanup(other_author.delete)
        self.addCleanup(other_user.delete)

        follow_request = FollowRequest.objects.create(
            from_author=other_author,
            to_author=self.author,
        )
        self.addCleanup(follow_request.delete)

        response = self.client.get(f"/api/authors/{self.author.id}/follow_requests")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "requests")
        self.assertEqual(len(payload["requests"]), 1)

        request_payload = payload["requests"][0]
        self.assertEqual(request_payload["type"], "follow")
        self.assertEqual(request_payload["actor"]["id"], f"http://testserver/api/authors/{other_author.id}")
        self.assertEqual(request_payload["object"]["id"], f"http://testserver/api/authors/{self.author.id}")
        self.assertIn("wants to follow", request_payload["summary"])

        # now we test usage with a user trying to read another users follows
        self.client.logout()
        self.client.force_login(other_user)

        response = self.client.get(f"/api/authors/{self.author.id}/follow_requests")
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.force_login(self.user)

    def test_following_return_valid(self):
        target_user = self.user_model.objects.create_user(
            username="target",
            password="targetpass",
        )
        target_author = Author.objects.create(
            user=target_user,
            display_name="Target",
            host="http://testserver",
        )
        self.addCleanup(target_author.delete)
        self.addCleanup(target_user.delete)

        self.author.following.add(target_author)

        response = self.client.get(f"/api/authors/{self.author.id}/following/{target_author.id}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], f"http://testserver/api/authors/{target_author.id}")

    def test_following_per_user_returns_404_if_not_following(self):
        target_user = self.user_model.objects.create_user(
            username="target2",
            password="targetpass2",
        )
        target_author = Author.objects.create(
            user=target_user,
            display_name="Target2",
            host="http://testserver",
        )
        self.addCleanup(target_author.delete)
        self.addCleanup(target_user.delete)

        response = self.client.get(f"/api/authors/{self.author.id}/following/{target_author.id}")
        self.assertEqual(response.status_code, 404)

    def test_following_per_user_forbidden_if_not_owner(self):
        target_user = self.user_model.objects.create_user(
            username="target3",
            password="targetpass3",
        )
        target_author = Author.objects.create(
            user=target_user,
            display_name="Target3",
            host="http://testserver",
        )
        self.addCleanup(target_author.delete)
        self.addCleanup(target_user.delete)

        self.author.following.add(target_author)
        another_user = self.user_model.objects.create_user(
            username="impersonator",
            password="impersonate",
        )
        another_author = Author.objects.create(
            user=another_user,
            display_name="Imposter",
            host="http://testserver",
        )
        self.addCleanup(another_author.delete)
        self.addCleanup(another_user.delete)

        self.client.logout()
        self.client.force_login(another_user)

        response = self.client.get(f"/api/authors/{self.author.id}/following/{target_author.id}")
        self.assertEqual(response.status_code, 403)

        self.client.logout()
        self.client.force_login(self.user)
