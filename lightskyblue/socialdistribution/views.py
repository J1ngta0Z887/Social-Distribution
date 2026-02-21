from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Author, AuthorProfile

@login_required
def home(request):
    return render(request, "socialdistribution/home.html")



User = get_user_model()

def public_author_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = AuthorProfile.objects.get_or_create(user=user)
    return render(request, "socialdistribution/profile.html", {
        "profile_user": user,
        "profile": profile,
    })






@login_required
def follow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me = get_object_or_404(Author, user=request.user)

    target = get_object_or_404(Author, id=author_id)

    if me.host != target.host:
        return HttpResponseForbidden("Can only follow local authors")

    if me.id == target.id:
        return HttpResponseBadRequest("Cannot follow yourself")

    me.following.add(target)
    return JsonResponse({"ok": True, "following": True, "target": str(target.id)})

@login_required
def unfollow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, id=author_id)

    me.following.remove(target)
    return JsonResponse({"ok": True, "following": False, "target": str(target.id)})

