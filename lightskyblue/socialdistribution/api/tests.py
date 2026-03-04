import json
from urllib import parse

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Author


# disclaimer of AI usage:
# many of these test cases are initially generated with Kimi 2.5, then cleaned up by hand
class APITests(TestCase):
    user_model = get_user_model()

    def setUp(self):
        self.test_user = self.user_model.objects.create(
            username="testuser",
            password="password",
        )
        self.test_author = Author.objects.create(
            user=self.test_user,
            display_name="Test Author",
            host="https://testauthor/",
            bio="A test author.",
            github_url="https://github.com/veryfaketestauthorsgithub",
            picture_url="http://example.com/testauthorsphoto.jpg",
        )

        self.other_user = self.user_model.objects.create(
            username="otheruser",
            password="password",
        )
        self.other_author = Author.objects.create(
            user=self.other_user,
            display_name="Other Author",
            host="https://otherauthor/",
            bio="The other author.",
            github_url="https://github.com/veryfakeotherauthorsgithub",
            picture_url="http://example.com/otherauthorsphoto.jpg",
        )

        self.client.force_login(self.test_user)

    def tearDown(self):
        pass

    """
    REGION https://uofa-cmput404.github.io/general/project.html#authors-api
    """

    def test_api_authors_get(self):
        """
        Test: GET /api/authors/
        Targets: local, remote
        """
        # Create multiple authors for pagination testing
        authors = []
        for i in range(5):
            user = self.user_model.objects.create(
                username=f"testuser{i}",
                password=f"testpass{i}",
            )
            author = Author.objects.create(
                user=user,
                display_name=f"Test Author {i}",
                host="http://testserver",
                bio=f"Bio for author {i}",
                github_url=f"https://github.com/testuser{i}",
                picture_url=f"http://example.com/pic{i}.jpg",
            )
            authors.append(author)
            self.addCleanup(user.delete)
            self.addCleanup(author.delete)

        # Test basic GET request
        response = self.client.get("/api/authors/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "authors")
        self.assertIn("authors", payload)
        self.assertIn("page", payload)
        self.assertIn("size", payload)

        # Check that all authors are returned (including existing ones)
        all_authors_count = Author.objects.count()
        self.assertEqual(len(payload["authors"]), all_authors_count)

        # Check author structure matches spec
        if payload["authors"]:
            author_data = payload["authors"][0]
            self.assertEqual(author_data["type"], "author")
            self.assertIn("id", author_data)
            self.assertIn("host", author_data)
            self.assertIn("displayName", author_data)
            self.assertIn("github", author_data)
            self.assertIn("profileImage", author_data)
            self.assertIn("web", author_data)

        # Test pagination with page and size parameters
        response = self.client.get("/api/authors/?page=1&size=2")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "authors")
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["size"], 2)
        self.assertEqual(len(payload["authors"]), 2)

        # Test second page
        response = self.client.get("/api/authors/?page=2&size=2")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["page"], 2)
        self.assertEqual(len(payload["authors"]), 2)

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#single-author-api
    """

    def test_api_authors_の_get(self):
        """
        Test: GET /api/authors/の
        """
        # Test GET for existing author
        author_id = self.test_author.id
        test_author_serialized = self.test_author.serialize()
        response = self.client.get(f"/api/authors/{author_id}/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "author")
        self.assertEqual(payload["id"], test_author_serialized["id"])
        self.assertEqual(payload["displayName"], self.test_author.display_name)
        self.assertEqual(payload["host"], test_author_serialized["host"])
        self.assertEqual(payload["github"], self.test_author.github_url)
        self.assertEqual(payload["profileImage"], self.test_author.picture_url)
        self.assertIn("web", payload)

        response = self.client.get(f"/api/authors/fakeid/")
        self.assertEqual(response.status_code, 404)

    def test_api_authors_の_put(self):
        """
        Test: PUT /api/authors/の
        """
        author_id = self.test_author.id

        update_data = {
            "bio": "Updated bio",
            "github": "https://github.com/updatedgithub",
            "profileImage": "http://example.com/updatedpic.jpg",
        }
        response = self.client.put(
            f"/api/authors/{author_id}/",
            data=json.dumps(update_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "author")
        self.assertEqual(payload["displayName"], self.test_author.display_name)
        self.assertEqual(payload["bio"], "Updated bio")
        self.assertEqual(payload["github"], "https://github.com/updatedgithub")
        self.assertEqual(payload["profileImage"], "http://example.com/updatedpic.jpg")

        # Verify changes persisted to database
        self.test_author.refresh_from_db()
        self.assertEqual(self.test_author.bio, "Updated bio")
        self.assertEqual(
            self.test_author.github_url, "https://github.com/updatedgithub"
        )
        self.assertEqual(
            self.test_author.picture_url, "http://example.com/updatedpic.jpg"
        )

        # Test partial update (only displayName)
        update_data = {"displayName": "Partially Updated Name"}
        response = self.client.put(
            f"/api/authors/{author_id}/",
            data=json.dumps(update_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify only displayName changed, others remain from previous update
        self.test_author.refresh_from_db()
        self.assertEqual(self.test_author.display_name, "Partially Updated Name")
        self.assertEqual(self.test_author.bio, "Updated bio")  # unchanged

        # Login as the test user but try to modify other_author
        response = self.client.put(
            f"/api/authors/{self.other_author.id}/",
            data=json.dumps({"displayName": "Hacked"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Verify other_author was not modified
        self.other_author.refresh_from_db()
        self.assertEqual(self.other_author.display_name, "Other Author")

        response = self.client.put(
            "/api/authors/fakeid/",
            data=json.dumps({"displayName": "Fake"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        # Test with empty request body (should succeed with no changes)
        response = self.client.put(
            f"/api/authors/{author_id}/",
            data="",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#following-api
    """

    def test_api_authors_の_following_get(self):
        """
        Test: GET api/authors/の/following
        """
        author_id = self.test_author.id

        # Test successful GET when user is the owner (empty following list initially)
        response = self.client.get(f"/api/authors/{author_id}/following/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "following")
        self.assertIn("authors", payload)
        self.assertEqual(len(payload["authors"]), 0)

        # Create some authors for the test author to follow
        followed_authors = []
        for i in range(3):
            user = self.user_model.objects.create(
                username=f"followeduser{i}",
                password=f"followedpass{i}",
            )
            author = Author.objects.create(
                user=user,
                display_name=f"Followed Author {i}",
                host="http://testserver",
                bio=f"Bio for followed author {i}",
                github_url=f"https://github.com/followeduser{i}",
                picture_url=f"http://example.com/followedpic{i}.jpg",
            )
            followed_authors.append(author)
            self.test_author.following.add(author)
            self.addCleanup(user.delete)
            self.addCleanup(author.delete)

        # Test GET with following list populated
        response = self.client.get(f"/api/authors/{author_id}/following/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "following")
        self.assertEqual(len(payload["authors"]), 3)

        # Verify structure of returned authors
        for author_data in payload["authors"]:
            self.assertEqual(author_data["type"], "author")
            self.assertIn("id", author_data)
            self.assertIn("host", author_data)
            self.assertIn("displayName", author_data)
            self.assertIn("github", author_data)
            self.assertIn("profileImage", author_data)
            self.assertIn("web", author_data)

        # Try to access other author's following list while logged in as test_user
        response = self.client.get(f"/api/authors/{self.other_author.id}/following/")
        self.assertEqual(response.status_code, 401)

    def test_api_authors_の_following_よ_get(self):
        """
        Test: GET api/authors/の/following/よ
        """
        author_id = self.test_author.id

        self.test_author.following.add(self.other_author)

        other_author_serialized = self.other_author.serialize()

        other_author_encoded_fqid = parse.quote(other_author_serialized["id"], safe="")
        response = self.client.get(
            f"/api/authors/{self.test_author.id}/following/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "author")
        self.assertIn("id", payload)
        self.assertIn("host", payload)
        self.assertIn("displayName", payload)
        self.assertEqual(payload["displayName"], other_author_serialized["displayName"])

        # now test when not following
        self.test_author.following.remove(self.other_author)
        response = self.client.get(
            f"/api/authors/{author_id}/following/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 404)

        # Test 401 when other author doesn't exist
        response = self.client.get(f"/api/authors/{author_id}/following/999999/")
        self.assertEqual(response.status_code, 404)

        # Test 401 when user is not the owner (unauthorized)
        response = self.client.get(
            f"/api/authors/{self.other_author.id}/following/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 401)

        # Test 401 when author_id is invalid
        response = self.client.get("/api/authors/invalidauthor/following/1/")
        self.assertEqual(response.status_code, 401)

        # Test with foreign author using encoded FQID
        foreign_user = self.user_model.objects.create(
            username="foreignuser",
            password="foreignpass",
        )
        foreign_author = Author.objects.create(
            user=foreign_user,
            display_name="Foreign Author",
            host="http://foreignhost.com/",
            bio="A foreign author.",
            github_url="https://github.com/foreignuser",
            picture_url="http://example.com/foreignpic.jpg",
        )
        self.test_author.following.add(foreign_author)
        self.addCleanup(foreign_user.delete)
        self.addCleanup(foreign_author.delete)

        foreign_fqid = parse.quote(
            f"http://foreignhost.com/api/authors/{foreign_author.id}", safe=""
        )
        response = self.client.get(
            f"/api/authors/{author_id}/following/{foreign_fqid}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["displayName"], foreign_author.display_name)

    def api_authors_の_following_よ_put(self):
        """
        Test: PUT api/authors/の/following/よ
        """
        # REQUIRE: Inbox API

    def test_api_authors_の_following_よ_delete(self):
        """
        Test: DELETE api/authors/の/following/よ
        """
        author_id = self.test_author.id
        other_author_serialized = self.other_author.serialize()
        other_author_encoded_fqid = parse.quote(other_author_serialized["id"], safe="")

        self.test_author.following.add(self.other_author)

        response = self.client.delete(
            f"/api/authors/{self.test_author.id}/following/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.test_author.following.filter(id=self.other_author.id).exists()
        )

        response = self.client.delete(
            f"/api/authors/{author_id}/following/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(f"/api/authors/{author_id}/following/999999/")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            f"/api/authors/{self.other_author.id}/following/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 401)

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#followers-api
    """

    def api_authors_の_followers_よ_get(self):
        """
        Test: GET api/authors/の/followers/よ
        """

    def api_authors_の_followers_よ_put(self):
        """
        Test: PUT api/authors/の/followers/よ
        """

    def api_authors_の_followers_よ_delete(self):
        """
        Test: DELETE api/authors/の/followers/よ
        """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#follow-request-api
    """

    def api_authors_の_followくrequests_get(self):
        """
        Test: GET api/authors/の/follow_requests
        """

    def api_authors_の_followくrequests_post(self):
        """
        Test: POST api/authors/の/inbox
        """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#entries-api
    """

    def api_authors_の_entries_よ_get(self):
        """
        Test: GET api/authors/の/entries/よ
        """

    def api_authors_の_entries_よ_put(self):
        """
        Test: PUT api/authors/の/entries/よ
        """

    def api_authors_の_entries_よ_delete(self):
        """
        Test: DELETE api/authors/の/entries/よ
        """

    def api_entries_よ_get(self):
        """
        Test: GET api/entries/よ
        """

    def api_authors_の_entries_get(self):
        """
        Test: GET api/authors/の/entries
        """

    def api_authors_の_entries_post(self):
        """
        Test: POST api/authors/の/entries
        """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#image-entries
    """

    def api_authors_の_entries_よ_image_get(self):
        """
        Test: GET api/authors/の/entries/よ/image
        """

    def api_entries_の_image_get(self):
        """
        Test: GET api/entries/の/image
        """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#comments-api
    """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#commented-api
    """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#likes-api
    """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#liked-api
    """

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#inbox-api
    """

    """
    ENDREGION
    """
