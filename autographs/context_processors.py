from .models import Tag

def header_filters(request):
    return {
        "all_tags": Tag.objects.order_by("name"),
        "selected_tag_ids": request.GET.getlist("tags"),
        "q": (request.GET.get("q") or "").strip(),
    }
