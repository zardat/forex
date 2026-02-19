"""
Custom API exceptions for Market API v1.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class PairNotFoundError(APIException):
    """Raised when a forex pair is not found or inactive."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Forex pair not found or inactive"
    default_code = "PAIR_NOT_FOUND"


class InvalidTimeframeError(APIException):
    """Raised when an invalid timeframe is provided."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid timeframe"
    default_code = "INVALID_TIMEFRAME"


class InvalidParameterError(APIException):
    """Raised when required parameters are missing or invalid."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid or missing required parameter"
    default_code = "INVALID_PARAMETER"