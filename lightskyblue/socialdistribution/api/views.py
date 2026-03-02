"""
The API's try to follow a `pull` and `push` methodology, with `pull`ing retrieving information
from an API's relevant model, and `push`ing updating the API's relevant model.
"""
from functools import wraps
from http.client import HTTPResponse
import json
from django.contrib.auth.models import User
from urllib.request import Request

from django.core.paginator import Paginator
# ref: https://stackoverflow.com/questions/16181188/django-doesnotexist
# just nicer for typing
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views import View
from ..models import Author, FollowRequest


def get_author_model_from_id(author_id: int | str) -> Author | None:
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


# ref: https://deepankarm.github.io/posts/type-safe-python-decorators/
# the purpose of this decorator is to make sure the user is authorized to access / modify
# the information at the route.
# this works elegantly, but still seems a bit like dark magic to me lol
def user_must_be_author(capture_name: str):
    """
    Decorator used to reduce the amount of boilerplate to ensure the requesting
    user has authorization to view / modify a given authors model.

    Usage example::

        @user_must_be_author(capture_name="author_id")
        def get(self, req: HTTPResponse):
            ...

    :param capture_name: Captured values name in the route that represents the author ID
    :type capture_name: str
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            user = self.request.user
            author_id = kwargs.get(capture_name)
            author = get_author_model_from_id(author_id)
            if not author:
                return JsonResponse({}, status=404)
            if user.id != author.user.id:
                return JsonResponse({}, status=401)
            return func(self, *args, **kwargs)

        return wrapper
    return decorator


class AuthorInboxAPI(View):
    """
    Route: /authors/{AUTHOR_SERIAL}/inbox
    Implements: https://uofa-cmput404.github.io/general/project.html#inbox-api
    Complete?: No

    Likely the most important api of our project (thus why it's at the top).
    It's very multi-faceted, taking on roles from other apis as per spec.
    """
    # NOTE: the authentication used here is NOT CORRECT yet. We
    # need to figure out a way to verify which nodes are allowed
    # to post to our nodes inbox
    def put(self, req: HTTPResponse, author_id: any):
        user = req.user
        if not user.is_authenticated:
            return JsonResponse({}, status=401)

        author = self._pull(author_id)
        if not author:
            return JsonResponse({}, status=404)

        if user.id != author.id:
            return JsonResponse({}, status=403)

        try:
            payload = json.loads(req.body.decode("utf-8")) if req.body else {}
        except json.JSONDecodeError:
            payload = {}



        self._push(author, payload)
        return JsonResponse(author.serialize(), safe=True)


class AuthorsAPI(View):
    """
    Route: /authors
    Implements: https://uofa-cmput404.github.io/general/project.html#authors-api
    Complete?: Pending
    """
    def _pull(self):
        return Author.objects.all()

    def get(self, req: HTTPResponse):
        authors = self._pull()
        try:
            page = req.GET.get('page', 1)
        except ValueError:
            page = 1
        try:
            size = req.GET.get('size', 10)
        except ValueError:
            size = 5

        # note: gpt-5.1-codex-mini(medium) taught me about the paginator
        # ref: https://docs.djangoproject.com/en/6.0/topics/pagination/
        paginator = Paginator(authors, size)
        page = paginator.get_page(page)

        resp = {}
        resp["type"] = "authors"
        # we add the page number and size here for easier debugging
        resp["page"] = page.number
        resp["size"] = page.paginator.per_page
        resp["authors"] = []
        for author in page.object_list:
            resp["authors"].append(author.serialize())

        return JsonResponse(resp)

class AuthorAPI(View):
    """
    Route: /author/{AUTHOR_SERIAL}/
    Implements: https://uofa-cmput404.github.io/general/project.html#single-author-api
    Complete?: Pending
    """
    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    def _push(self, author: Author, new_values: dict):
        author.update_profile(new_values)

    def get(self, req, author_id):
        author = self._pull(author_id)
        if not author:
            return JsonResponse({}, status=404)
        return JsonResponse(author.serialize(), safe=True)

    @user_must_be_author("author_id")
    def put(self, req: HTTPResponse, author_id: any):
        author = self._pull(author_id)
        try:
            payload = json.loads(req.body.decode("utf-8")) if req.body else {}
        except json.JSONDecodeError:
            payload = {}

        self._push(author, payload)
        return JsonResponse(author.serialize(), safe=True)

# per https://uofa-cmput404.github.io/general/project.html#following-api
class AuthorFollowingsAPI(View):
    """
    Route: /authors/{AUTHOR_SERIAL}/following
    Implements: https://uofa-cmput404.github.io/general/project.html#following-api
    Complete?: Pending
    """
    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    @user_must_be_author("author_id")
    def get(self, req: HTTPResponse, author_id: any):
        author = self._pull(author_id)

        resp = {}
        resp["type"] = "following"
        resp["authors"] = []
        for author in author.following.all():
            resp["authors"].append(author.serialize())
        return JsonResponse(resp)

class AuthorFollowingPerUserAPI(View):
    """
    Route: /authors/{AUTHOR_SERIAL}/following/{FOREIGN_AUTHOR_FQID}
    Implements: https://uofa-cmput404.github.io/general/project.html#following-api
    Complete?: Pending
    """
    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    @user_must_be_author("author_id")
    def get(self, req: HTTPResponse, author_id: any, target_author_id: any):
        author = self._pull(author_id)
        target_author = self._pull(target_author_id)

        if not target_author:
            return JsonResponse({}, status=404)
        if not author.is_following(target_author):
            return JsonResponse({}, status=404)

        return JsonResponse(target_author.serialize(), safe=True)


class AuthorFollowersAPI(View):
    """
    Route: /authors/{AUTHOR_SERIAL}/followers/{FOREIGN_AUTHOR_FQID}
    Implements: https://uofa-cmput404.github.io/general/project.html#followers-api
    Complete?: Pending
    """
    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    def get(self, req: HTTPResponse, author_id: int):
        author = self._pull(author_id)
        if not author:
            return JsonResponse({}, status=403)

        resp = {}
        resp["type"] = "followers"
        resp["authors"] = []
        for author in author.followers.all():
            resp["authors"].append(author.serialize())
        return JsonResponse(resp)
    pass


# per https://uofa-cmput404.github.io/general/project.html#follow-request-api
class AuthorFollowRequestAPI(View):
    """
    Route: /authors/{AUTHOR_SERIAL}/follow_requests
    Implements: https://uofa-cmput404.github.io/general/project.html#follow-request-api
    Complete?: Pending
    """
    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    @user_must_be_author("author_id")
    def get(self, req: HTTPResponse, author_id: any):
        author = self._pull(author_id)
        follow_requests = FollowRequest.objects.filter(to_author=author)

        resp = {}
        resp["type"] = "requests"
        resp["requests"] = []
        for follow_request in follow_requests:
            resp["requests"].append(follow_request.serialize())
        return JsonResponse(resp)
