from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.serializers import LogoutSerializer, RegisterSerializer, UserSerializer


@extend_schema(tags=["accounts"])
class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Does NOT log them in automatically. The client must call the login 
    endpoint immediately after to obtain access and refresh tokens.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["accounts"])
class MeView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """Log out a user by blacklisting their refresh token."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        request=LogoutSerializer,
        responses={
            205: OpenApiResponse(description="Logged out"),
            400: OpenApiResponse(description="Missing or invalid refresh token"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "invalid or expired refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_205_RESET_CONTENT)