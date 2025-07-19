from django.urls import path
from users.views import (
    UserRegisterAPIView, UserLoginAPIView, UserRefreshAPIView,
    UserListAPIView, UserRetrieveAPIView, UserUpdateAPIView, UserDestroyAPIView
)
from users.apps import UsersConfig

app_name = UsersConfig.name

urlpatterns = [
    path('register/', UserRegisterAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='login'),
    path('token/refresh/', UserRefreshAPIView.as_view(), name='token_refresh'),

    path('', UserListAPIView.as_view(), name='user_list'),
    path('<int:pk>/', UserRetrieveAPIView.as_view(), name='user_retrieve'),
    path('<int:pk>/update/', UserUpdateAPIView.as_view(), name='user_update'),
    path('<int:pk>/delete/', UserDestroyAPIView.as_view(), name='user_delete'),
]