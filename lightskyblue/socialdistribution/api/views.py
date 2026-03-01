# note:
# all apis must be written in an extensible fashion when pulling or pushing
# data from or to the database, so that they can be reused in the user-facing
# views.
from http.client import HTTPResponse
import json
from urllib.request import Request

from django.core.paginator import Paginator
# ref: https://stackoverflow.com/questions/16181188/django-doesnotexist
# just nicer for typing
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views import View
from ..models import Author


def get_author_model_from_id(author_id: int | str) -> Author | None:
    if author_id.isdigit():
        return Author.objects.get(id=int(author_id))
    else:
        return Author.objects.get(display_name=author_id)

def user_is_author(user, author: Author) -> bool:
    return user.id == author.id

# per https://uofa-cmput404.github.io/general/project.html#authors-api
class AuthorsAPI(View):

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

# per https://uofa-cmput404.github.io/general/project.html#single-author-api
class AuthorAPI(View):

    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    def _push(self, author: Author, new_values: dict):
        author.update_profile(new_values)

    def get(self, req, author_id):
        try:
            author = self._pull(author_id)
        except ObjectDoesNotExist:
            return JsonResponse({})
        return JsonResponse(author.serialize(), safe=True)

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

# per https://uofa-cmput404.github.io/general/project.html#following-api
class AuthorFollowingsAPI(View):

    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    def get(self, req: HTTPResponse, author_id: any):
        author = self._pull(author_id)

        if not author:
            return JsonResponse({})
        elif not user_is_author(req.user, author):
            return JsonResponse({}, status=403)

        resp = {}
        resp["type"] = "following"
        resp["authors"] = []
        for author in author.following.all():
            resp["authors"].append(author.serialize())
        return JsonResponse(resp)

# per https://uofa-cmput404.github.io/general/project.html#following-api (foreign authors
# TODO: implement
class AuthorFollowingPerUserAPI(View):

    pass



# per https://uofa-cmput404.github.io/general/project.html#followers-api
class AuthorFollowersAPI(View):

    def _pull(self, author_id: int | str) -> Author | None:
        return get_author_model_from_id(author_id)

    def get(self, req: HTTPResponse, author_id: int):
        author = self._pull(author_id)
        if not author:
            return JsonResponse({})

        resp = {}
        resp["type"] = "followers"
        resp["authors"] = []
        for author in author.followers.all():
            resp["authors"].append(author.serialize())
        return JsonResponse(resp)
    pass


# per https://uofa-cmput404.github.io/general/project.html#follow-request-api
class AuthorFollowRequestAPI(View):

    def get(self, req: HTTPResponse, author_id: any):
        pass