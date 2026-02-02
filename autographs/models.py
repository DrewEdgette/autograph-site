import secrets
import string
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models

from PIL import Image, ImageOps


ALPHABET = string.ascii_letters + string.digits  # a-zA-Z0-9 (62 chars)

def generate_autograph_id(length: int = 11) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def build_thumbnail(uploaded_file, max_size=(600, 600), fmt="JPEG", quality=80) -> ContentFile:
    """
    Create a resized/compressed thumbnail (fits within max_size, keeps aspect ratio).
    Fixes EXIF rotation (common with iPhone photos).
    """
    uploaded_file.open("rb")

    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)

    # JPEG can't store alpha; convert if needed
    if fmt.upper() in ("JPEG", "JPG") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(
        buf,
        format=fmt,
        quality=quality,
        optimize=True,
        progressive=True,
    )
    return ContentFile(buf.getvalue())


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

    # NEW: thumbnail stored separately in Spaces
    thumb = models.ImageField(
        upload_to="autographs/thumbs/",
        blank=True,
        null=True,
        editable=False,
    )

    price = models.DecimalField(max_digits=8, decimal_places=2)

    size = models.CharField(
        max_length=50,
        default="8×10 in (20×25 cm)",
    )

    tags = models.ManyToManyField(Tag, blank=True, related_name="autographs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        creating = self._state.adding

        old_image_name = None
        if not creating and self.pk:
            old_image_name = (
                Autograph.objects.filter(pk=self.pk)
                .values_list("image", flat=True)
                .first()
            )

        image_changed = creating or (old_image_name and self.image and old_image_name != self.image.name)

        # Build a thumbnail only when creating, when the image changes, or if thumb is missing.
        if self.image and (creating or image_changed or not self.thumb):
            thumb_file = build_thumbnail(self.image, max_size=(600, 600), fmt="JPEG", quality=80)
            thumb_name = f"{self.pk}.jpg"  # uses your 11-char id
            self.thumb.save(thumb_name, thumb_file, save=False)

        super().save(*args, **kwargs)


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
