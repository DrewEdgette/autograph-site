from .models import Autograph, Tag
from django.shortcuts import render, get_object_or_404
from django.db.models import Case, When
from rapidfuzz import fuzz, process
from django.core.cache import cache


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


FUZZ_THRESHOLD = 60
FUZZ_LIMIT = 200
CACHE_SECONDS = 120


def results(request):
    q = (request.GET.get("q") or "").strip()
    q_norm = q.casefold()  # better than lower() for case-insensitive matching
    tag_ids = request.GET.getlist("tags")

    autographs = Autograph.objects.all()

    if tag_ids:
        autographs = autographs.filter(tags__id__in=tag_ids).distinct()

    if q:
        if len(q_norm) < 2:
            autographs = Autograph.objects.none()
        else:
            candidates_qs = autographs

            if len(q_norm) >= 3:
                narrowed = candidates_qs.filter(name__icontains=q_norm[:3])
                if narrowed.exists():
                    candidates_qs = narrowed

            cache_key = f"cand:{hash((tuple(sorted(tag_ids)), q_norm[:3] if len(q_norm) >= 3 else 'all'))}"
            candidates = cache.get(cache_key)

            if candidates is None:
                candidates = list(candidates_qs.values_list("id", "name"))
                cache.set(cache_key, candidates, CACHE_SECONDS)

            matches = process.extract(
                q_norm,
                candidates,
                processor=lambda x: (x[1] or "").casefold(),
                scorer=fuzz.WRatio,
                limit=FUZZ_LIMIT,
            )

            matched_ids = [m[0][0] for m in matches if m[1] >= FUZZ_THRESHOLD]

            if matched_ids:
                order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(matched_ids)])
                autographs = Autograph.objects.filter(id__in=matched_ids).order_by(order)
            else:
                autographs = Autograph.objects.none()

    all_tags = Tag.objects.order_by("name")

    return render(request, "home.html", {
        "autographs": autographs,
        "q": q,  # keep original for displaying in the input
        "all_tags": all_tags,
        "selected_tag_ids": tag_ids,
    })




def contact(request):
    return render(request, "contact.html")


def autograph_detail(request, pk):
    autograph = get_object_or_404(Autograph, pk=pk)
    return render(request, "detail.html", {"autograph": autograph})