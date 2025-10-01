from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, UserProfile
from .serializers import (
    UserSerializer, UserProfileSerializer,
    UserRegistrationSerializer, LoginSerializer
)
from .permissions import IsOwnerOrReadOnly


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'message': 'Account created successfully'
        }, status=status.HTTP_201_CREATED)

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


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']
    refresh = RefreshToken.for_user(user)

    response = Response({
        'user': UserSerializer(user).data,
        'access': str(refresh.access_token),
        'message': 'Login successful'
    })

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
