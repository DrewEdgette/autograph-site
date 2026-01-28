from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = os.getenv("DJANGO_ENV_FILE", str(BASE_DIR / ".env"))
load_dotenv(ENV_FILE)


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "t", "yes", "y", "on")


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default).strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


ENVIRONMENT = os.getenv("DJANGO_ENV", "development").strip().lower()
IS_PROD = ENVIRONMENT in ("prod", "production")

# SECRET_KEY must come from env in prod
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if IS_PROD and not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY is required in production.")
if not SECRET_KEY:
    # Dev fallback only (do not rely on this in prod)
    SECRET_KEY = "dev-only-insecure-secret-key"

DEBUG = env_bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default="localhost,127.0.0.1,[::1]" if not IS_PROD else ""
)

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", default="")

# Helpful fallback: if you forgot CSRF_TRUSTED_ORIGINS in prod, derive from ALLOWED_HOSTS
if IS_PROD and not CSRF_TRUSTED_ORIGINS:
    _skip = {"localhost", "127.0.0.1", "[::1]"}
    _derived = []
    for h in ALLOWED_HOSTS:
        if h in _skip:
            continue
        # avoid obvious non-host values
        if "." in h and not h.startswith("["):
            _derived.append(f"https://{h}")
    CSRF_TRUSTED_ORIGINS = _derived


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 2FA (django-two-factor-auth + django-otp)
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",

    # DigitalOcean Spaces support (django-storages)
    "storages",

    "autographs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # 2FA
    "django_otp.middleware.OTPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "autographs.context_processors.header_filters",
            ],
        },
    },
]

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "admin:index"
LOGOUT_REDIRECT_URL = "two_factor:login"

# Explicit (default is True): patch Django admin to use the 2FA login flow
TWO_FACTOR_PATCH_ADMIN = True

WSGI_APPLICATION = "config.wsgi.application"

# Database (env-driven; works for both dev + prod)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "autographs_dev"),
        "USER": os.environ.get("POSTGRES_USER", "autographs_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]
else:
    STATICFILES_DIRS = []


# Media + storage (default: local filesystem; prod can switch to DO Spaces)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# DigitalOcean Spaces configuration (optional; enable by setting DO_SPACES_BUCKET)
DO_SPACES_BUCKET = os.getenv("DO_SPACES_BUCKET", "").strip()
DO_SPACES_REGION = os.getenv("DO_SPACES_REGION", "").strip()
DO_SPACES_ENDPOINT_URL = os.getenv("DO_SPACES_ENDPOINT_URL", "").strip()
DO_SPACES_CDN_DOMAIN = os.getenv("DO_SPACES_CDN_DOMAIN", "").strip()

if DO_SPACES_BUCKET:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.getenv("DO_SPACES_KEY", ""),
            "secret_key": os.getenv("DO_SPACES_SECRET", ""),
            "bucket_name": DO_SPACES_BUCKET,
            "region_name": DO_SPACES_REGION or None,
            "endpoint_url": DO_SPACES_ENDPOINT_URL or None,
            # simplest: public objects + stable URLs
            "default_acl": "public-read",
            "querystring_auth": False,
            "file_overwrite": False,
        },
    }

    # Serve media from CDN if available; otherwise via endpoint/bucket URL
    if DO_SPACES_CDN_DOMAIN:
        MEDIA_URL = f"https://{DO_SPACES_CDN_DOMAIN.rstrip('/')}/"
    elif DO_SPACES_ENDPOINT_URL:
        MEDIA_URL = f"{DO_SPACES_ENDPOINT_URL.rstrip('/')}/{DO_SPACES_BUCKET}/"


# Production-only security (env-driven, safe defaults)
if IS_PROD:
    # Required when you're behind a proxy (nginx/Cloudflare) so Django knows the original scheme was HTTPS
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

    # Redirect + secure cookies (make nginx do the heavy lifting; Django enforces too)
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=True)

    # HSTS (default OFF to avoid painful mistakes; enable once you're confident)
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", default=False)

    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    REFERRER_POLICY = "same-origin"

    # Good practice in prod so stale static files don’t get served
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    }
else:
    # In dev, keep these false unless you explicitly want them on
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
    CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=False)



LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        # This is where unhandled 500s get logged
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django": {"handlers": ["console"], "level": "INFO"},
    },
}