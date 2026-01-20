from django.contrib import admin
from .models import Autograph, Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]

@admin.register(Autograph)
class AutographAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "created_at"]
    list_filter = ["created_at", "tags"]
    search_fields = ["id", "name", "tags__name"]
    filter_horizontal = ["tags"]  # nicer UI for ManyToMany
    ordering = ["-created_at"]
