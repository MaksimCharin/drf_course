from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.models import User
from users.serializers import UserSerializer, UserRegisterSerializer


class UserRegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (AllowAny,)


class UserLoginAPIView(TokenObtainPairView):
    permission_classes = (AllowAny,)


class UserRefreshAPIView(TokenRefreshView):
    permission_classes = (AllowAny,)


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class UserRetrieveAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        obj = super().get_object()
        if obj != self.request.user and not self.request.user.is_staff:
            self.permission_denied(
                self.request, message="Вы не можете просматривать чужой профиль."
            )
        return obj


class UserUpdateAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        obj = super().get_object()
        if obj != self.request.user and not self.request.user.is_staff:
            self.permission_denied(
                self.request, message="Вы не можете обновлять чужой профиль."
            )
        return obj


class UserDestroyAPIView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        obj = super().get_object()
        if obj != self.request.user and not self.request.user.is_staff:
            self.permission_denied(
                self.request, message="Вы не можете удалять чужой профиль."
            )
        return obj
