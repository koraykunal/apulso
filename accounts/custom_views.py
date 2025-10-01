from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.middleware.csrf import get_token


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.COOKIES.get('refresh_token')

    if not refresh_token:
        return Response({
            'error': 'Refresh token not found in cookies'
        }, status=status.HTTP_401_UNAUTHORIZED)

    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)

        response = Response({
            'access': new_access_token,
            'message': 'Token refreshed successfully'
        })

        if hasattr(refresh, 'token') and refresh.token != refresh_token:
            # Production-ready cookie settings
            is_production = not request.META.get('HTTP_HOST', '').startswith('localhost') and not request.META.get('HTTP_HOST', '').startswith('127.0.0.1')

            response.set_cookie(
                'refresh_token',
                str(refresh),
                max_age=7 * 24 * 60 * 60,  # 7 days
                httponly=True,
                secure=is_production,  # True for production HTTPS
                samesite='None' if request.META.get('HTTP_ORIGIN') else 'Lax',
                path='/'
            )

        return response

    except (TokenError, InvalidToken):
        response = Response({
            'error': 'Invalid or expired refresh token'
        }, status=status.HTTP_401_UNAUTHORIZED)

        response.delete_cookie('refresh_token', path='/')
        return response


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    refresh_token = request.COOKIES.get('refresh_token')

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (TokenError, InvalidToken):
            pass

    response = Response({
        'message': 'Logged out successfully'
    })

    response.delete_cookie('refresh_token', path='/')
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    return Response({
        'csrfToken': get_token(request)
    })