from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from two_factor.urls import urlpatterns as tf_urls
import os
from django.contrib import admin
from two_factor.admin import AdminSiteOTPRequired

admin.site.__class__ = AdminSiteOTPRequired

# Allow env override, but normalize it for Django's path()
ADMIN_PATH = os.environ.get("DJANGO_ADMIN_PATH", "admin/").strip()
ADMIN_PATH = ADMIN_PATH.lstrip("/")  # no leading slash

if not ADMIN_PATH.endswith("/"):
    ADMIN_PATH += "/"

urlpatterns = [
    # 2FA routes (provides /account/login/, /account/two_factor/setup/, etc.)
    path("", include(tf_urls)),

    # Your app
    path("", include("autographs.urls")),

    # Admin (will be patched to use the 2FA login when TWO_FACTOR_PATCH_ADMIN=True)
    path(ADMIN_PATH, admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
