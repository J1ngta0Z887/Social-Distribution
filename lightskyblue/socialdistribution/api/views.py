import json
import typing as typing
from functools import wraps
from json.decoder import JSONDecodeError
from urllib.parse import unquote
from urllib.request import Request

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse
from django.views import View

from ..models import Author, Entry, FollowRequest


def get_author_model_from_id(author_id: str) -> Author | None:
    """
    Retrieves an `Author` from the database based on the provided author ID.
    Supports either number ID or the authors display name.

    :param author_id: Either the number ID or the display name of the author.
    :type author_id: int | str
    :return: The `Author` if found; otherwise, returns `None`.
    :rtype: Author | None
    """
    try:
        if author_id.isdigit():
            return Author.objects.get(id=int(author_id))
        else:
            return Author.objects.get(display_name=author_id)
    except ObjectDoesNotExist:
        return None


def get_model_author_from_hostname_and_id(foreign_author_id: str):
    """
    Retrieves an `Author` from the database based on a percent-encoded foreign author FQID.
    The FQID is a URL like http://example.com/api/authors/{AUTHOR_SERIAL}.

    :param foreign_author_id: A percent-encoded URL of the foreign author.
    :type foreign_author_id: str
    :return: The `Author` if found locally; otherwise, returns `None`.
    :rtype: Author | None
    """
    from urllib.parse import unquote, urlparse

    try:
        decoded_id = unquote(foreign_author_id)
        parsed = urlparse(decoded_id)

        hostname = parsed.netloc
        if not hostname:
            return None

        path = parsed.path.rstrip("/")
        path_parts = path.split("/")
        if not path_parts:
            return None

        last_directory = path_parts[-1]
        authors = Author.objects.filter(host__contains=hostname, id=last_directory)
        if len(authors) < 1:
            return None
        return authors[0]
    except (ValueError, IndexError):
        return None


def get_entry_from_hostname_and_id(foreign_entry_id: str):
    from urllib.parse import unquote, urlparse

    try:
        decoded_id = unquote(foreign_entry_id)
        parsed = urlparse(decoded_id)

        hostname = parsed.netloc
        if not hostname:
            return None

        path = parsed.path.rstrip("/")
        path_parts = path.split("/")
        if not path_parts:
            return None

        last_directory = path_parts[-1]
        entries = Entry.objects.filter(id=last_directory)
        for entry in entries:
            if hostname in entry.author.host:
                return entry
        return None
        # if len(entries) < 1:
        #     return None
        # return entries[0]

    except (ValueError, IndexError):
        return None


def user_must_be_author(capture_name: str):
    """
    Decorator used to reduce the amount of boilerplate to ensure the requesting
    user has authorization to view / modify a given authors model.

    Usage example::

        @user_must_be_author(capture_name="author_id")
        def get(self, req: HttpRequest):
            ...

    :param capture_name: Captured values name in the route that represents the author ID
    :type capture_name: str
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            user = self.request.user
            author_id = kwargs.get(capture_name)
            if not author_id or type(author_id) is not str:
                return JsonResponse({}, status=401)
            author = get_author_model_from_id(author_id)
            if not author:
                return JsonResponse({}, status=401)
            if user.id != author.user.id:
                return JsonResponse({}, status=401)
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


"""
REGION https://uofa-cmput404.github.io/general/project.html#authors-api
"""


class api_authors(View):
    def _pull(self):
        return Author.objects.all().order_by("id")

    def get(self, req: HttpRequest):
        authors = self._pull()
        try:
            page = req.GET.get("page", 1)
        except ValueError:
            page = 1
        try:
            size = req.GET.get("size", 10)
        except ValueError:
            size = 5

        paginator = Paginator(authors, size)
        page = paginator.get_page(page)

        resp = {}
        resp["type"] = "authors"
        resp["page"] = page.number
        resp["size"] = page.paginator.per_page
        resp["authors"] = []
        for author in page.object_list:
            resp["authors"].append(author.serialize())

        return JsonResponse(resp)

        return resp


"""
ENDREGION
"""


"""
REGION https://uofa-cmput404.github.io/general/project.html#single-author-api
"""


class api_authors_の(View):
    def _pull(self, author_id: str) -> Author | None:
        return get_author_model_from_id(author_id)

    def _push(self, author: Author, new_values: dict):
        # update profile only selectively updates based on available keys
        author.update_profile(new_values)

    def get(self, req: HttpRequest, author_id: str):
        author = self._pull(author_id)

        if author is None:
            return JsonResponse({}, status=404)
        return JsonResponse(author.serialize(), status=200)

    @user_must_be_author("author_id")
    def put(self, req: HttpRequest, author_id: str):
        author = self._pull(author_id)
        if not author:
            return JsonResponse({}, status=404)
        try:
            payload = json.loads(req.body.decode("utf-8")) if req.body else {}
        except JSONDecodeError:
            payload = {}

        self._push(author, payload)
        return JsonResponse(author.serialize())


"""
ENDREGION
"""

"""
REGION https://uofa-cmput404.github.io/general/project.html#following-api
"""


class api_authors_の_following(View):
    def _pull(self, author_id: str):
        author = get_author_model_from_id(author_id)
        if not author:
            return []
        return author.following.all()

    @user_must_be_author("author_id")
    def get(self, req: HttpRequest, author_id: str):
        following_list = self._pull(author_id)

        resp = {}
        resp["type"] = "following"
        resp["authors"] = []
        for author in following_list:
            resp["authors"].append(author.serialize())
        return JsonResponse(resp)


class api_authors_の_following_よ(View):
    def _pull(self, author_id: str):
        pass

    @user_must_be_author("author_id")
    def get(self, req: HttpRequest, author_id: str, other_author_id: str):
        curr_author = get_author_model_from_id(author_id)
        other_other = get_model_author_from_hostname_and_id(other_author_id)
        if (
            not curr_author
            or not other_other
            or not curr_author.following.filter(id=other_other.id).exists()
        ):
            return JsonResponse({}, status=404)

        return JsonResponse(other_other.serialize())

    @user_must_be_author("author_id")
    def put(self, req: HttpRequest, author_id: str, other_author_id: str):
        # REQUIRE: Inbox API
        pass

    @user_must_be_author("author_id")
    def delete(self, req: HttpRequest, author_id: str, other_author_id: str):
        pass
        curr_author = get_author_model_from_id(author_id)
        other_other = get_model_author_from_hostname_and_id(other_author_id)
        if (
            not curr_author
            or not other_other
            or not curr_author.following.filter(id=other_other.id).exists()
        ):
            return JsonResponse({}, status=404)

        curr_author.following.remove(other_other)
        return JsonResponse({})


"""
ENDREGION
"""

"""
REGION https://uofa-cmput404.github.io/general/project.html#followers-api
"""


class api_authors_の_followers_よ(View):
    @user_must_be_author("author_id")
    def get(self, req: HttpRequest, author_id: str, other_author_id: str):
        # todo: support foreign node
        curr_author = get_author_model_from_id(author_id)
        other_other = get_model_author_from_hostname_and_id(other_author_id)
        if (
            not curr_author
            or not other_other
            or not curr_author.followers.filter(id=other_other.id).exists()
        ):
            return JsonResponse({}, status=404)
        return JsonResponse(other_other.serialize())

    @user_must_be_author("author_id")
    def put(self, req: HttpRequest, author_id: str, other_author_id: str):
        # REQUIRE: Inbox API
        pass

    @user_must_be_author("author_id")
    def delete(self, req: HttpRequest, author_id: str, other_author_id: str):
        curr_author = get_author_model_from_id(author_id)
        other_other = get_model_author_from_hostname_and_id(other_author_id)
        if (
            not curr_author
            or not other_other
            or not curr_author.followers.filter(id=other_other.id).exists()
        ):
            return JsonResponse({}, status=404)

        curr_author.followers.remove(other_other)
        return JsonResponse(other_other.serialize())


"""
ENDREGION
"""

"""
REGION https://uofa-cmput404.github.io/general/project.html#follow-request-api
"""


class api_authors_の_followくrequests(View):
    @user_must_be_author("author_id")
    def get(self, req: HttpRequest, author_id: str):
        author = typing.cast(Author, get_author_model_from_id(author_id))

        follow_reqs = FollowRequest.objects.filter(to_author=author)

        resp = []
        for follow in follow_reqs:
            resp.append(follow.serialize())

        return JsonResponse(resp, safe=False)


"""
ENDREGION
"""

"""
REGION https://uofa-cmput404.github.io/general/project.html#entries-api
"""


class api_authors_の_entries_よ(View):
    """
    Note: this version is for local node authors
    """

    def _pull(self, entry_id: str) -> Entry | None:
        if not entry_id.isdigit():
            return None
        entry = Entry.objects.all().filter(id=entry_id)
        if len(entry) < 1:
            return None
        return entry[0]

    def get(self, req: HttpRequest, author_id: str, entry_id: str):
        author = get_author_model_from_id(author_id)
        if not author or not entry_id.isdigit():
            return JsonResponse({}, status=404)
        entry = self._pull(entry_id)
        if not entry:
            return JsonResponse({}, status=404)
        if entry.visibility == "FRIENDS" and entry.author.id != author.id:
            return JsonResponse({}, status=401)

        return JsonResponse(entry.serialize())

    @user_must_be_author("author_id")
    def delete(self, req: HttpRequest, author_id: str, entry_id: str):
        author = typing.cast(Author, get_author_model_from_id(author_id))
        entry = self._pull(entry_id)
        if not entry:
            return JsonResponse({}, status=404)
        if entry.author.id != author.id:
            return JsonResponse({}, status=401)
        entry.delete()
        return JsonResponse({})

    @user_must_be_author("author_id")
    def put(self, req: HttpRequest, author_id: str, entry_id: str):
        author = typing.cast(Author, get_author_model_from_id(author_id))
        entry = self._pull(entry_id)
        if not entry:
            return JsonResponse({}, status=404)
        if entry.author.id != author.id:
            return JsonResponse({}, status=401)

        try:
            data = json.loads(req.body)
        except json.JSONDecodeError:
            return JsonResponse({}, status=400)

        entry.update(data)

        entry.save()
        return JsonResponse(entry.serialize())


class api_entries_よ(View):
    def get(self, req: HttpRequest, entry_id: str):
        user = req.user
        author = None
        if user.is_authenticated:
            author = get_author_model_from_id(str(user.id))

        entry = get_entry_from_hostname_and_id(entry_id)
        if not entry:
            return JsonResponse({}, status=404)

        if entry.visibility == "FRIENDS":
            if (
                author != entry.author
                and not entry.author.followers.filter(
                    host=author.host, display_name=author.display_name
                ).exists()
            ):
                return JsonResponse({}, status=401)

        return JsonResponse(entry.serialize())


"""
ENDREGION
"""
