from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-id',
]

CORS_EXPOSE_HEADERS = ['X-Session-ID']