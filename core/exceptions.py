import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError

logger = logging.getLogger('core')


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code
        
        if response.status_code == 401:
            response.data['error'] = 'Authentication credentials were not provided or are invalid'
        elif response.status_code == 403:
            response.data['error'] = 'You do not have permission to perform this action'
        elif response.status_code == 404:
            response.data['error'] = 'The requested resource was not found'
        elif response.status_code == 429:
            response.data['error'] = 'Too many requests. Please try again later'
        
        return response

    if isinstance(exc, ValidationError):
        logger.warning(f"Validation error: {exc}")
        return Response(
            {'error': 'Validation error', 'details': str(exc), 'status_code': 400},
            status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(exc, IntegrityError):
        logger.error(f"Database integrity error: {exc}")
        return Response(
            {'error': 'Database integrity error', 'status_code': 400},
            status=status.HTTP_400_BAD_REQUEST
        )

    logger.exception(f"Unhandled exception: {exc}")
    return Response(
        {'error': 'An unexpected error occurred', 'status_code': 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
