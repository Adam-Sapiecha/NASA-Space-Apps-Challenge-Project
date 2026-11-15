"""Production entry point for a prefixed reverse proxy and the Pages frontend."""
import os

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount


def create_deployment(application, prefix='', origins=()):
    prefix = prefix.rstrip('/')
    if prefix and (not prefix.startswith('/') or '..' in prefix or '?' in prefix or '#' in prefix):
        raise ValueError('Use an absolute URL path prefix.')
    if origins:
        application.add_middleware(CORSMiddleware, allow_origins=list(origins),
                                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
    if not prefix:
        return application
    # Support proxies that retain the mount path as well as proxies that strip it.
    # Mounting preserves correct StaticFiles path handling and ASGI lifespan.
    return Starlette(routes=[Mount(prefix, app=application), Mount('/', app=application)],
                     lifespan=application.router.lifespan_context)


from backend.main import app as api_app

app = create_deployment(api_app, os.environ.get('SPHEREX_URL_PREFIX', ''),
                        [origin.strip() for origin in os.environ.get('SPHEREX_CORS_ORIGINS', '').split(',') if origin.strip()])
