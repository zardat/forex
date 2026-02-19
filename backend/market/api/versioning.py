"""
API versioning configuration.
"""
from rest_framework.versioning import URLPathVersioning


class MarketAPIVersioning(URLPathVersioning):
    """
    Versioning scheme for Market API.
    Extracts version from URL path: /api/v1/market/...
    """
    default_version = 'v1'
    allowed_versions = ['v1']
    version_param = 'version'