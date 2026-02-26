from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.db.models import Q
from socialdistribution.models import Author, AuthorProfile, Entry, Comment
from socialdistribution.forms import AuthorProfileForm, EntryForm, CommentForm
from django.views.decorators.http import require_POST
