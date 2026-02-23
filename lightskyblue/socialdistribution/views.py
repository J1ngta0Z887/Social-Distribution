from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth import get_user_model
from .models import Author, AuthorProfile, Entry
from .forms import AuthorProfileForm, EntryForm


@login_required
def home(request):
    return render(request, "socialdistribution/home.html")


@login_required
def authors_list(request):
    me, _ = Author.objects.get_or_create(user=request.user)
    authors = Author.objects.filter(host=me.host)
    return render(request, "socialdistribution/authors.html", {
        "authors": authors,
        "my_author": me
    })


@login_required
def follow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me, _ = Author.objects.get_or_create(user=request.user)
    target = get_object_or_404(Author, id=author_id)

    if me.host != target.host:
        return HttpResponseForbidden("Can only follow local authors")

    if me.id == target.id:
        return HttpResponseBadRequest("Cannot follow yourself")

    me.following.add(target)
    return redirect("authors_list")


@login_required
def unfollow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me, _ = Author.objects.get_or_create(user=request.user)
    target = get_object_or_404(Author, id=author_id)

    me.following.remove(target)
    return redirect("authors_list")



@login_required
def my_entries(request):
    me, _ = Author.objects.get_or_create(user=request.user)
    entries = Entry.objects.filter(author=me).order_by("-created_at")
    return render(request, "socialdistribution/my_entries.html", {
        "my_author": me,
        "entries": entries,
    })


@login_required
def create_entry(request):
    me, _ = Author.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = me
            entry.save()
            return redirect("feed")
    else:
        form = EntryForm()

    return render(request, "socialdistribution/create_entry.html", {
        "my_author": me,
        "form": form,
    })


@login_required
def author_entries(request, author_id):
    me, _ = Author.objects.get_or_create(user=request.user)
    author = get_object_or_404(Author, id=author_id)

    # local-only constraint (fits your "local authors" story)
    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors' entries")

    # show visibility rules (simple version)
    qs = Entry.objects.filter(author=author).order_by("-created_at")

    # If you're not the author, hide UNLISTED (optional)
    if me.id != author.id:
        qs = qs.exclude(visibility="UNLISTED")

    return render(request, "socialdistribution/author_entries.html", {
        "my_author": me,
        "author": author,
        "entries": qs,
    })


@login_required
def feed(request):
    me, _ = Author.objects.get_or_create(user=request.user)

    following_ids = list(me.following.values_list("id", flat=True))
    following_ids.append(me.id)  # include my own posts

    entries = Entry.objects.filter(
        author__id__in=following_ids,
        author__host=me.host
    ).exclude(
        visibility="UNLISTED"
    ).order_by("-created_at")

    return render(request, "socialdistribution/feed.html", {
        "my_author": me,
        "entries": entries,
    })

User = get_user_model()


@login_required
def public_author_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = AuthorProfile.objects.get_or_create(user=user)
    author = get_object_or_404(Author, user=user)

    me, _ = Author.objects.get_or_create(user=request.user)

    # Optional local-only rule
    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    entries = Entry.objects.filter(author=author).order_by("-created_at")

    # Optional: hide unlisted unless it's your own profile
    if request.user != user:
        entries = entries.exclude(visibility="UNLISTED")

    return render(request, "socialdistribution/profile.html", {
        "profile_user": user,
        "profile": profile,
        "author": author,
        "entries": entries,
        "my_author": me,
    })


@login_required
def edit_profile(request):
    profile, _ = AuthorProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = AuthorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("public_author_profile", username=request.user.username)
    else:
        form = AuthorProfileForm(instance=profile)

    return render(request, "socialdistribution/edit_profile.html", {
        "form": form,
        "profile": profile,
    })