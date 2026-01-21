from django.contrib import admin
from .models import Autograph, Tag
from .models import SiteSetting

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(Autograph)
class AutographAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "created_at"]
    list_filter = ["created_at", "tags"]
    search_fields = ["id", "name", "description", "tags__name"]  # <-- add
    filter_horizontal = ["tags"]
    ordering = ["-created_at"]

    # optional: control layout on the edit form
    fields = ("id", "name", "description", "image", "price", "tags", "created_at")
    readonly_fields = ("id", "created_at")


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("id", "shipping_cost_display", "updated_at")
