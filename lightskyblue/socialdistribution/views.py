from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Author, AuthorProfile
from .forms import AuthorProfileForm
from .models import Author
from django.shortcuts import render, get_object_or_404, redirect

@login_required
def home(request):
    return render(request, "socialdistribution/home.html")

@login_required
def authors_list(request):
    me = get_object_or_404(Author, user=request.user)
    authors = Author.objects.filter(host=me.host)  # local authors
    return render(request, "socialdistribution/authors.html", {
        "authors": authors,
        "my_author": me
    })



User = get_user_model()

def public_author_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = AuthorProfile.objects.get_or_create(user=user)
    return render(request, "socialdistribution/profile.html", {
        "profile_user": user,
        "profile": profile,
    })



@login_required
def edit_profile(request):
    # Ensure the logged-in user always has a profile row
    profile, _ = AuthorProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = AuthorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # after saving, go to public profile page
            return redirect("public_author_profile", username=request.user.username)
    else:
        form = AuthorProfileForm(instance=profile)

    return render(request, "socialdistribution/edit_profile.html", {
        "form": form,
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
    return redirect({"ok": True, "following": True, "target": str(target.id)})

@login_required
def unfollow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, id=author_id)

    me.following.remove(target)
    return redirect({"ok": True, "following": False, "target": str(target.id)})

@login_required
def following_feed(request):
    me = get_object_or_404(Author, user=request.user)
    following_ids = me.following.values_list("id", flat=True)

    posts = Post.objects.filter(author__id__in=following_ids).order_by("-published")
    return render(request, "socialdistribution/following_feed.html", {
        "posts": posts,
        "my_author": me
    })