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

    image = models.ImageField(upload_to="autographs/")

    price = models.DecimalField(max_digits=8, decimal_places=2)

    tags = models.ManyToManyField(Tag, blank=True, related_name="autographs")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # default newest first

    def __str__(self) -> str:
        return self.name
