from .models import Autograph, Tag, SiteSetting
from django.shortcuts import render, get_object_or_404
from django.db.models import Case, When
from rapidfuzz import fuzz, process
from django.core.cache import cache
from django.core.paginator import Paginator
import re


# views.py
import re
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Case, When
from django.shortcuts import render
from rapidfuzz import fuzz

from .models import Autograph, Tag


def home(request):
    q = (request.GET.get("q") or "").strip()
    tag_ids = request.GET.getlist("tags")
    sort = (request.GET.get("sort") or "").strip()  # NEW
    page_number = request.GET.get("page", 1)

    autographs = Autograph.objects.all().prefetch_related("tags")

    if q:
        autographs = autographs.filter(name__icontains=q)

    if tag_ids:
        autographs = autographs.filter(tags__id__in=tag_ids).distinct()

    # NEW: price sorting
    if sort == "price_asc":
        autographs = autographs.order_by("price", "name")
    elif sort == "price_desc":
        autographs = autographs.order_by("-price", "name")
    # else: keep default Meta.ordering (newest-first)

    paginator = Paginator(autographs, 9)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "autographs": page_obj.object_list,
        "q": q,
        "sort": sort,  # NEW
        "all_tags": Tag.objects.order_by("name"),
        "selected_tag_ids": tag_ids,
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/_autograph_page.html", context)

    return render(request, "home.html", context)


def results(request):
    q = (request.GET.get("q") or "").strip()
    q_norm = q.casefold()
    tag_ids = request.GET.getlist("tags")
    sort = (request.GET.get("sort") or "").strip()  # NEW
    page_number = request.GET.get("page", 1)

    autographs = Autograph.objects.all().prefetch_related("tags")

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
                cache.set(cache_key, candidates, 120)

            ranked = []
            q_word = q_norm
            q_re = re.compile(rf"\b{re.escape(q_word)}\b", re.IGNORECASE)

            for pk, name in candidates:
                name_norm = (name or "").casefold()
                if not name_norm:
                    continue

                score = fuzz.WRatio(q_norm, name_norm)
                if score < 60:
                    continue

                tokens = re.findall(r"[a-z0-9]+", name_norm)

                if name_norm == q_norm:
                    tier = 0
                elif any(t == q_norm for t in tokens):
                    tier = 1
                elif name_norm.startswith(q_norm + " "):
                    tier = 2
                elif any(t.startswith(q_norm) for t in tokens):
                    tier = 3
                elif q_re.search(name_norm):
                    tier = 4
                elif q_norm in name_norm:
                    tier = 5
                else:
                    tier = 6

                ranked.append((pk, tier, -score, len(name_norm), name_norm))

            ranked.sort(key=lambda x: (x[1], x[2], x[3], x[4]))
            matched_ids = [pk for pk, *_ in ranked[:200]]

            if matched_ids:
                base_qs = Autograph.objects.filter(id__in=matched_ids).prefetch_related("tags")

                # NEW: if sorting by price, sort within the matched set
                if sort == "price_asc":
                    autographs = base_qs.order_by("price", "name")
                elif sort == "price_desc":
                    autographs = base_qs.order_by("-price", "name")
                else:
                    order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(matched_ids)])
                    autographs = base_qs.order_by(order)
            else:
                autographs = Autograph.objects.none()

    # NEW: if no q (no ranking path), still allow sort
    if not q:
        if sort == "price_asc":
            autographs = autographs.order_by("price", "name")
        elif sort == "price_desc":
            autographs = autographs.order_by("-price", "name")

    paginator = Paginator(autographs, 9)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "autographs": page_obj.object_list,
        "q": q,
        "sort": sort,  # NEW
        "all_tags": Tag.objects.order_by("name"),
        "selected_tag_ids": tag_ids,
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/_autograph_page.html", context)

    return render(request, "home.html", context)




def contact(request):
    return render(request, "contact.html")


def newsletter(request):
    return render(request, "newsletter.html")


def autograph_detail(request, pk):
    autograph = get_object_or_404(Autograph, pk=pk)
    site_settings = SiteSetting.get()
    
    return render(request, "detail.html", {
        "autograph": autograph,
        "shipping_cost_display": site_settings.shipping_cost_display,
    })