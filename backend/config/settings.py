import os

DEBUG = os.environ.get("DEBUG", "0") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY") or ("dev-only-key" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("Set SECRET_KEY (or DEBUG=1 for local development)")
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

INSTALLED_APPS = ["corsheaders", "routing"]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
if os.environ.get("CORS_ALLOW_ALL") == "1":
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {}
USE_TZ = True
