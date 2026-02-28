# note:
# all apis must be written in an extensible fashion when pulling or pushing
# data from or to the database, so that they can be reused in the user-facing
# views.
from http.client import HTTPResponse

from django.http import JsonResponse
from django.views.generic import ListView
from django.forms.models import model_to_dict
from ..models import Author


class AuthorsView(ListView):

    def _pull(self):
        return Author.objects.all()

    def get(self, req):
        data = self._pull().last().serialize()
        #print(data.user.username)
        return JsonResponse(data, safe=False)

