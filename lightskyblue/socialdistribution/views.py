from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Author, AuthorProfile, Entry
from .forms import AuthorProfileForm, EntryForm
from django.views.decorators.http import require_POST
from .models import Comment

from .forms import CommentForm




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

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors' entries")

    qs = Entry.objects.filter(author=author).order_by("-created_at")

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
    following_ids.append(me.id)
    friend_ids = list(me.following.filter(following=me).values_list("id", flat=True))

    #allows viewing of all public entries and unlisted/friends-only entries of authors you are following
    entries = Entry.objects.filter(
        author__host=me.host
    ).filter(
        Q(visibility="PUBLIC") |
        Q(visibility="UNLISTED", author__id__in=following_ids) |
        Q(visibility="FRIENDS", author__id__in=friend_ids)
    ).order_by("-created_at")

    return render(request, "socialdistribution/feed.html", {
        "my_author": me,
        "entries": entries,
    })


@login_required
def public_author_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = AuthorProfile.objects.get_or_create(user=user)
    author = get_object_or_404(Author, user=user)

    me, _ = Author.objects.get_or_create(user=request.user)

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    # If it's your own profile, show all your entries (optional)
    if request.user == user:
        entries = Entry.objects.filter(author=author).order_by("-created_at")
    else:
        # Non-followers (and everyone else) only see PUBLIC posts
        entries = Entry.objects.filter(author=author, visibility="PUBLIC").order_by("-created_at")

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

@login_required
def edit_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)

    # Task 13: Security Check - Other authors cannot modify my entries
    # We compare the Entry's author's user to the Request's user
    if entry.author.user != request.user:
        return HttpResponseForbidden("You are not the author of this entry.")

    if request.method == "POST":
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("my_entries") # Redirects to the list of user's entries
    else:
        form = EntryForm(instance=entry)

    # Reusing the create_entry template, or you can make a specific edit_entry.html
    return render(request, "socialdistribution/create_entry.html", {
        "form": form,
        "title": "Edit Entry"
    })

@login_required
def delete_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)

    # Task 13: Security Check
    if entry.author.user != request.user:
        return HttpResponseForbidden("You are not the author of this entry.")

    if request.method == "POST":
        entry.delete()
        return redirect("my_entries")

    # Task 23: Author can see entry before deletion (It's passed in context)
    return render(request, "socialdistribution/confirm_delete.html", {"entry": entry})

def can_access_entry(me: Author, entry: Entry) -> bool:
    if entry.author.host != me.host:
        return False
    if entry.visibility == "UNLISTED":
        return False
    allowed_ids = set(me.following.values_list("id", flat=True))
    allowed_ids.add(me.id)
    return entry.author_id in allowed_ids


@require_POST
@login_required
def add_comment(request, entry_id):
    me, _ = Author.objects.get_or_create(user=request.user)
    entry = get_object_or_404(Entry, id=entry_id)

    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot comment on this entry.")

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment.")

    comment = form.save(commit=False)
    comment.entry = entry
    comment.author = me
    comment.save()

    return redirect(request.POST.get("next") or "feed")


@require_POST
@login_required
def toggle_entry_like(request, entry_id):
    me, _ = Author.objects.get_or_create(user=request.user)
    entry = get_object_or_404(Entry, id=entry_id)

    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot like this entry.")

    if entry.likes.filter(id=me.id).exists():
        entry.likes.remove(me)
    else:
        entry.likes.add(me)

    return redirect(request.POST.get("next") or "feed")


@require_POST
@login_required
def toggle_comment_like(request, comment_id):
    me, _ = Author.objects.get_or_create(user=request.user)
    comment = get_object_or_404(Comment, id=comment_id)
    entry = comment.entry

    # same access rule as the entry
    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot like this comment.")

    if comment.likes.filter(id=me.id).exists():
        comment.likes.remove(me)
    else:
        comment.likes.add(me)

    return redirect(request.POST.get("next") or "feed")