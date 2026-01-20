from django.shortcuts import render
from .models import Autograph, Tag
from django.shortcuts import render, get_object_or_404


def home(request):
    q = (request.GET.get("q") or "").strip()
    tag_ids = request.GET.getlist("tags")

    autographs = Autograph.objects.all()

    if q:
        autographs = autographs.filter(name__icontains=q)

    if tag_ids:
        autographs = autographs.filter(tags__id__in=tag_ids).distinct()

    return render(request, "home.html", {
        "autographs": autographs,
        "q": q,
        "all_tags": Tag.objects.order_by("name"),
        "selected_tag_ids": tag_ids,
    })


def results(request):
    q = (request.GET.get("q") or "").strip()
    tag_ids = request.GET.getlist("tags")  # e.g. ?tags=1&tags=3

    autographs = Autograph.objects.all()

    if q:
        autographs = autographs.filter(name__icontains=q)

    if tag_ids:
        autographs = autographs.filter(tags__id__in=tag_ids).distinct()

    all_tags = Tag.objects.order_by("name")

    return render(request, "home.html", {
        "autographs": autographs,
        "q": q,
        "all_tags": all_tags,
        "selected_tag_ids": tag_ids,  # list of strings
    })



def contact(request):
    return render(request, "contact.html")


def autograph_detail(request, pk):
    autograph = get_object_or_404(Autograph, pk=pk)
    return render(request, "detail.html", {"autograph": autograph})