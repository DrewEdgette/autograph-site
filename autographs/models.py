import secrets
import string
from django.db import models

ALPHABET = string.ascii_letters + string.digits  # a-zA-Z0-9 (62 chars)

def generate_autograph_id(length: int = 11) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Autograph(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=11,
        editable=False,
        unique=True,
        default=generate_autograph_id,
    )

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to="autographs/")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    tags = models.ManyToManyField(Tag, blank=True, related_name="autographs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name




class SiteSetting(models.Model):
    shipping_cost_display = models.CharField(
        max_length=64,
        default="€13 EUR / $15 USD",
        help_text='Shown on the site, e.g. "€13 EUR / $15 USD".'
    )

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # enforce singleton (only one row)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Site settings"