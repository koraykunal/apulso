from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, UserProfile, EmailVerificationToken, EmailChangeRequest
from .serializers import (
    UserSerializer, UserProfileSerializer,
    UserRegistrationSerializer, LoginSerializer
)
from .permissions import IsOwnerOrReadOnly
from .utils import send_verification_email, send_email_change_verification


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            send_verification_email(user, request)
        except Exception as e:
            user.delete()
            return Response({
                'error': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'message': 'Registration successful! Please check your email to verify your account.',
            'email': user.email
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']

    if not user.is_verified:
        return Response({
            'error': 'Your email is not verified. Please check your email.',
            'email': user.email,
            'requires_verification': True
        }, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)

    response = Response({
        'user': UserSerializer(user).data,
        'access': str(refresh.access_token),
        'message': 'Login successful'
    })

    is_production = not request.META.get('HTTP_HOST', '').startswith('localhost') and not request.META.get('HTTP_HOST', '').startswith('127.0.0.1')

    response.set_cookie(
        'refresh_token',
        str(refresh),
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        secure=is_production,
        samesite='None' if request.META.get('HTTP_ORIGIN') else 'Lax',
        path='/'
    )

    return response


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    token_str = request.data.get('token')

    if not token_str:
        return Response({
            'error': 'Token is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = EmailVerificationToken.objects.get(token=token_str)
    except EmailVerificationToken.DoesNotExist:
        return Response({
            'error': 'Invalid verification token'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if user is already verified
    if token.user.is_verified:
        refresh = RefreshToken.for_user(token.user)
        response = Response({
            'user': UserSerializer(token.user).data,
            'access': str(refresh.access_token),
            'message': 'Email already verified. You can now login.',
            'already_verified': True
        })

        is_production = not request.META.get('HTTP_HOST', '').startswith('localhost') and not request.META.get('HTTP_HOST', '').startswith('127.0.0.1')

        response.set_cookie(
            'refresh_token',
            str(refresh),
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            secure=is_production,
            samesite='None' if request.META.get('HTTP_ORIGIN') else 'Lax',
            path='/'
        )

        return response

    if not token.is_valid():
        if token.is_used:
            return Response({
                'error': 'This verification link has already been used. Your email may already be verified.'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'error': 'This verification link has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)

    user = token.user
    user.is_verified = True
    user.save()

    token.is_used = True
    token.save()

    refresh = RefreshToken.for_user(user)
    response = Response({
        'user': UserSerializer(user).data,
        'access': str(refresh.access_token),
        'message': 'Email verified successfully'
    })

    is_production = not request.META.get('HTTP_HOST', '').startswith('localhost') and not request.META.get('HTTP_HOST', '').startswith('127.0.0.1')

    response.set_cookie(
        'refresh_token',
        str(refresh),
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        secure=is_production,
        samesite='None' if request.META.get('HTTP_ORIGIN') else 'Lax',
        path='/'
    )

    return response


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_email(request):
    email = request.data.get('email')

    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if user.is_verified:
        return Response({
            'error': 'Email is already verified'
        }, status=status.HTTP_400_BAD_REQUEST)

    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)

    try:
        send_verification_email(user, request)
    except Exception as e:
        return Response({
            'error': 'Failed to send verification email'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'message': 'Verification email sent successfully'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_email_change(request):
    new_email = request.data.get('new_email')

    if not new_email:
        return Response({
            'error': 'New email is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=new_email).exists():
        return Response({
            'error': 'This email is already in use'
        }, status=status.HTTP_400_BAD_REQUEST)

    EmailChangeRequest.objects.filter(user=request.user, is_used=False).update(is_used=True)

    email_change = EmailChangeRequest.objects.create(
        user=request.user,
        new_email=new_email
    )

    try:
        send_email_change_verification(request.user, new_email, email_change.token)
    except Exception as e:
        email_change.delete()
        return Response({
            'error': 'Failed to send verification email'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'message': f'Verification email sent to {new_email}. Please check your inbox.'
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email_change(request):
    token_str = request.data.get('token')

    if not token_str:
        return Response({
            'error': 'Token is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        email_change = EmailChangeRequest.objects.get(token=token_str)
    except EmailChangeRequest.DoesNotExist:
        return Response({
            'error': 'Invalid verification token'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not email_change.is_valid():
        return Response({
            'error': 'Token has expired or already been used'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email_change.new_email).exists():
        return Response({
            'error': 'This email is already in use'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = email_change.user
    user.email = email_change.new_email
    user.save()

    email_change.is_used = True
    email_change.save()

    return Response({
        'message': 'Email updated successfully',
        'email': user.email
    })
