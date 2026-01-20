from django.shortcuts import render
from .models import Autograph
from django.shortcuts import render, get_object_or_404


def home(request):
    autographs = Autograph.objects.all()
    return render(request, "home.html", {"autographs": autographs})


def results(request):
    q = (request.GET.get("q") or "").strip()

    autographs = Autograph.objects.all()
    if q:
        autographs = autographs.filter(name__icontains=q)  # adjust fields as needed

    return render(request, "home.html", {
        "autographs": autographs,
        "q": q,
    })


def contact(request):
    return render(request, "contact.html")


def autograph_detail(request, pk):
    autograph = get_object_or_404(Autograph, pk=pk)
    return render(request, "detail.html", {"autograph": autograph})