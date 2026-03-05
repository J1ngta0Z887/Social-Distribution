import json
from urllib import parse

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Author, Entry, FollowRequest


# disclaimer of AI usage:
# many of these test cases are initially generated with some open source model,
# then cleaned up by hand
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

        response = self.client.get("/api/authors/fakeid/")
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

    def test_api_authors_の_followers_よ_get(self):
        """
        Test: GET api/authors/の/followers/よ
        """
        author_id = self.test_author.id

        self.test_author.followers.add(self.other_author)

        other_author_serialized = self.other_author.serialize()
        other_author_encoded_fqid = parse.quote(other_author_serialized["id"], safe="")

        response = self.client.get(
            f"/api/authors/{self.test_author.id}/followers/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 200)

        self.test_author.followers.remove(self.other_author)
        response = self.client.get(
            f"/api/authors/{author_id}/followers/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(f"/api/authors/{author_id}/followers/999999/")
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            f"/api/authors/{self.other_author.id}/followers/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.get("/api/authors/invalidauthor/followers/1/")
        self.assertEqual(response.status_code, 401)

    def api_authors_の_followers_よ_put(self):
        """
        Test: PUT api/authors/の/followers/よ
        """

    def test_api_authors_の_followers_よ_delete(self):
        """
        Test: DELETE api/authors/の/followers/よ
        """
        author_id = self.test_author.id

        other_author_serialized = self.other_author.serialize()
        other_author_encoded_fqid = parse.quote(other_author_serialized["id"], safe="")

        self.test_author.followers.add(self.other_author)

        response = self.client.delete(
            f"/api/authors/{self.test_author.id}/followers/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.test_author.followers.filter(id=self.other_author.id).exists()
        )

        response = self.client.delete(
            f"/api/authors/{author_id}/followers/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(f"/api/authors/{author_id}/followers/999999/")
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            f"/api/authors/{self.other_author.id}/followers/{other_author_encoded_fqid}/"
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.delete("/api/authors/invalidauthor/followers/1/")
        self.assertEqual(response.status_code, 401)

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#follow-request-api
    """

    def test_api_authors_の_followくrequests_get(self):
        """
        Test: GET api/authors/の/follow_requests
        """
        author_id = self.test_author.id

        # Test GET when there are no follow requests
        response = self.client.get(f"/api/authors/{author_id}/follow_requests/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(len(payload), 0)

        # Create follow requests from other authors to test_author
        follow_requests = []
        for i in range(3):
            user = self.user_model.objects.create(
                username=f"follower{i}",
                password=f"followerpass{i}",
            )
            author = Author.objects.create(
                user=user,
                display_name=f"Follower {i}",
                host="http://testserver",
                bio=f"Bio for follower {i}",
                github_url=f"https://github.com/follower{i}",
                picture_url=f"http://example.com/follower{i}.jpg",
            )
            follow_req = FollowRequest.objects.create(
                from_author=author,
                to_author=self.test_author,
                status="PENDING",
            )
            follow_requests.append((user, author, follow_req))
            self.addCleanup(user.delete)
            self.addCleanup(author.delete)

        # Test GET with follow requests in the database
        response = self.client.get(f"/api/authors/{author_id}/follow_requests/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(len(payload), 3)

        # Verify structure of returned follow requests
        for follow_req_data in payload:
            self.assertEqual(follow_req_data["type"], "follow")
            self.assertIn("summary", follow_req_data)
            self.assertIn("actor", follow_req_data)
            self.assertIn("object", follow_req_data)
            self.assertEqual(follow_req_data["actor"]["type"], "author")
            self.assertEqual(follow_req_data["object"]["type"], "author")

        # Test unauthorized access - try to access other author's follow requests
        response = self.client.get(
            f"/api/authors/{self.other_author.id}/follow_requests/"
        )
        self.assertEqual(response.status_code, 401)

    def api_authors_の_followくrequests_post(self):
        """
        Test: POST api/authors/の/inbox
        """
        # REQUIRE: Inbox API

    """
    ENDREGION
    """

    """
    REGION https://uofa-cmput404.github.io/general/project.html#entries-api
    """

    def test_api_authors_の_entries_よ_get(self):
        """
        Test: GET api/authors/の/entries/よ
        """
        entry = Entry.objects.create(
            author=self.test_author,
            title="Test Entry",
            content="This is test content for the entry.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        self.addCleanup(entry.delete)

        response = self.client.get(
            f"/api/authors/{self.test_author.id}/entries/{entry.id}"
        )
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "entry")
        self.assertEqual(payload["title"], "Test Entry")
        self.assertEqual(payload["content"], "This is test content for the entry.")
        self.assertEqual(payload["contentType"], "text/plain")
        self.assertEqual(payload["visibility"], "PUBLIC")

        response = self.client.get(
            f"/api/authors/{self.test_author.id}/entries/fakeentryid"
        )
        self.assertEqual(response.status_code, 404)

        entry_friends = Entry.objects.create(
            author=self.test_author,
            title="Friends Only Entry",
            content="This entry is for friends only.",
            content_type="text/plain",
            visibility="FRIENDS",
        )
        self.addCleanup(entry_friends.delete)

        response = self.client.get(
            f"/api/authors/{self.other_author.id}/entries/{entry_friends.id}"
        )
        self.assertEqual(response.status_code, 401)

    def test_api_authors_の_entries_よ_delete(self):
        """
        Test: DELETE api/authors/の/entries/よ
        """
        entry = Entry.objects.create(
            author=self.test_author,
            title="Test Entry to Delete",
            content="This entry will be deleted.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        entry_id = entry.id
        self.addCleanup(entry.delete)

        response = self.client.delete(
            f"/api/authors/{self.test_author.id}/entries/{entry_id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Entry.objects.filter(id=entry_id).exists())

        response = self.client.delete(
            f"/api/authors/{self.test_author.id}/entries/{entry_id}"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            f"/api/authors/{self.test_author.id}/entries/fakeentryid"
        )
        self.assertEqual(response.status_code, 404)

        entry_other = Entry.objects.create(
            author=self.other_author,
            title="Other Author Entry",
            content="This is another author's entry.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        self.addCleanup(entry_other.delete)

        response = self.client.delete(
            f"/api/authors/{self.test_author.id}/entries/{entry_other.id}"
        )
        self.assertEqual(response.status_code, 401)

    def test_api_authors_の_entries_よ_put(self):
        """
        Test: PUT api/authors/の/entries/よ
        """
        entry = Entry.objects.create(
            author=self.test_author,
            title="Original Title",
            content="Original content.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        entry_id = entry.id
        self.addCleanup(entry.delete)

        response = self.client.put(
            f"/api/authors/{self.test_author.id}/entries/{entry_id}",
            data=json.dumps(
                {
                    "title": "Updated Title",
                    "content": "# Updated content.",
                    "visibility": "FRIENDS",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["title"], "Updated Title")
        self.assertEqual(payload["content"], "# Updated content.")

        entry.refresh_from_db()
        self.assertEqual(entry.title, "Updated Title")

        response = self.client.put(f"/api/authors/{self.test_author.id}/entries/999999")
        self.assertEqual(response.status_code, 404)

        response = self.client.put(
            f"/api/authors/{self.test_author.id}/entries/fakeentryid"
        )
        self.assertEqual(response.status_code, 404)

        entry_other = Entry.objects.create(
            author=self.other_author,
            title="Other Author Entry",
            content="This is another author's entry.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        self.addCleanup(entry_other.delete)

        response = self.client.put(
            f"/api/authors/{self.test_author.id}/entries/{entry_other.id}",
            data=json.dumps({"title": "Changed Title"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        response = self.client.put(
            f"/api/authors/{self.test_author.id}/entries/{entry_id}",
            data="invalid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_entries_よ_get(self):
        """
        Test: GET api/entries/よ
        """
        entry = Entry.objects.create(
            author=self.test_author,
            title="Test Entry",
            content="This is a test entry.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        self.addCleanup(entry.delete)
        entry_serialized = entry.serialize()
        entry_serialized_id = parse.quote(entry_serialized["id"], safe="")
        response = self.client.get(f"/api/entries/{entry_serialized_id}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "entry")
        self.assertEqual(payload["id"], entry_serialized["id"])
        self.assertEqual(payload["title"], "Test Entry")
        self.assertEqual(payload["content"], "This is a test entry.")
        self.assertEqual(payload["contentType"], "text/plain")
        self.assertEqual(payload["visibility"], "PUBLIC")

        response = self.client.get("/api/entries/fakeentryid")
        self.assertEqual(response.status_code, 404)

        entry_friends = Entry.objects.create(
            author=self.other_author,
            title="Friends Only Entry",
            content="This entry is for friends only.",
            content_type="text/plain",
            visibility="FRIENDS",
        )
        self.addCleanup(entry_friends.delete)

        entry_friends_serialized_id = parse.quote(entry_friends.serialize()["id"])
        response = self.client.get(f"/api/entries/{entry_friends_serialized_id}")
        self.assertEqual(response.status_code, 401)

    def test_api_authors_の_entries_get(self):
        """
        Test: GET api/authors/の/entries
        """
        entry_public = Entry.objects.create(
            author=self.test_author,
            title="Public Entry",
            content="This is a public entry.",
            content_type="text/plain",
            visibility="PUBLIC",
        )
        self.addCleanup(entry_public.delete)

        entry_unlisted = Entry.objects.create(
            author=self.test_author,
            title="Unlisted Entry",
            content="This is an unlisted entry.",
            content_type="text/plain",
            visibility="UNLISTED",
        )
        self.addCleanup(entry_unlisted.delete)

        entry_friends = Entry.objects.create(
            author=self.test_author,
            title="Friends Entry",
            content="This is a friends-only entry.",
            content_type="text/plain",
            visibility="FRIENDS",
        )
        self.addCleanup(entry_friends.delete)

        entry_deleted = Entry.objects.create(
            author=self.test_author,
            title="Deleted Entry",
            content="This is a deleted entry.",
            content_type="text/plain",
            visibility="DELETED",
        )
        self.addCleanup(entry_deleted.delete)

        response = self.client.get(f"/api/authors/{self.test_author.id}/entries/")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["type"], "entries")
        self.assertIn("page", payload)
        self.assertIn("size", payload)
        self.assertIn("entries", payload)

        response = self.client.get("/api/authors/fakeauthorid/entries/")
        self.assertEqual(response.status_code, 404)

        self.client.logout()

        response = self.client.get(f"/api/authors/{self.test_author.id}/entries/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 1)

        self.client.force_login(self.test_user)

        response = self.client.get(f"/api/authors/{self.test_author.id}/entries/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 4)

        self.client.force_login(self.other_user)

        response = self.client.get(f"/api/authors/{self.test_author.id}/entries/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 1)

        self.test_author.followers.add(self.other_author)

        response = self.client.get(f"/api/authors/{self.test_author.id}/entries/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 2)

        self.test_author.following.add(self.other_author)

        response = self.client.get(f"/api/authors/{self.test_author.id}/entries/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 3)

        self.test_author.following.remove(self.other_author)
        self.other_author.following.remove(self.test_author)

        for i in range(15):
            entry = Entry.objects.create(
                author=self.test_author,
                title=f"Entry {i}",
                content=f"Content {i}",
                content_type="text/plain",
                visibility="PUBLIC",
            )
            self.addCleanup(entry.delete)

        for i in range(1, 4):
            response = self.client.get(
                f"/api/authors/{self.test_author.id}/entries?page={i}&size=5"
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(len(payload["entries"]), 5)
            self.assertEqual(payload["size"], 5)
            self.assertEqual(payload["page"], i)

        response = self.client.get(
            f"/api/authors/{self.test_author.id}/entries?page=2&size=5"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["entries"]), 5)

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

    def test_api_authors_の_entries_よ_comments_get(self):
        """
        Test: GET api/authors/の/entries/よ/comments
        """

    def api_entries_の_comments_get(self):
        """
        Test: GET api/entries/の/comments
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
