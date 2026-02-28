# note:
# all apis must be written in an extensible fashion when pulling or pushing
# data from or to the database, so that they can be reused in the user-facing
# views.
from http.client import HTTPResponse
from urllib.request import Request

from django.core.paginator import Paginator
# ref: https://stackoverflow.com/questions/16181188/django-doesnotexist
# just nicer for typing
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views import View
from ..models import Author


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
    def _pull(self, author_id) -> Author:
        return Author.objects.get(id=author_id)

    def get(self, req, author_id):
        try:
            author = self._pull(author_id)
        except ObjectDoesNotExist:
            return JsonResponse({})
        return JsonResponse(author.serialize(), safe=True)
