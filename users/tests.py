import datetime
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserAPITestCase(APITestCase):

    def setUp(self):
        self.user_password = "test_password123"
        self.user = User.objects.create_user(
            email="test_user@example.com", password=self.user_password, is_active=True
        )
        self.admin_user = User.objects.create_superuser(
            email="admin_user@example.com", password="admin_password123"
        )

        response = self.client.post(
            reverse("users:login"),
            {"email": "test_user@example.com", "password": self.user_password},
        )
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

        self.client.force_authenticate(user=self.user)

    def test_user_registration(self):
        """Тестирование регистрации нового пользователя"""
        data = {"email": "new_user@example.com", "password": "new_password123"}
        self.client.force_authenticate(user=None)
        response = self.client.post(reverse("users:register"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new_user@example.com").exists())

    def test_user_login(self):
        """Тестирование входа пользователя"""
        self.client.force_authenticate(user=None)
        response = self.client.post(
            reverse("users:login"),
            {"email": "test_user@example.com", "password": self.user_password},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_user_list_access(self):
        """Тестирование доступа к списку пользователей"""
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_user_retrieve_self(self):
        """Тестирование получения своего профиля"""
        response = self.client.get(
            reverse("users:user_retrieve", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test_user@example.com")

    def test_user_retrieve_other_forbidden(self):
        """Тестирование попытки получить чужой профиль (запрещено)"""
        other_user = User.objects.create_user(
            email="other@example.com", password="other_password"
        )
        response = self.client.get(
            reverse("users:user_retrieve", kwargs={"pk": other_user.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_self(self):
        """Тестирование обновления своего профиля"""
        data = {"city": "New York"}
        response = self.client.patch(
            reverse("users:user_update", kwargs={"pk": self.user.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.city, "New York")

    def test_user_update_other_forbidden(self):
        """Тестирование попытки обновить чужой профиль (запрещено)"""
        other_user = User.objects.create_user(
            email="another@example.com", password="another_password"
        )
        data = {"city": "London"}
        response = self.client.patch(
            reverse("users:user_update", kwargs={"pk": other_user.pk}), data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_self(self):
        """Тестирование удаления своего профиля"""
        initial_user_count = User.objects.count()
        response = self.client.delete(
            reverse("users:user_delete", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), initial_user_count - 1)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_user_delete_other_forbidden(self):
        """Тестирование попытки удалить чужой профиль (запрещено)"""
        other_user = User.objects.create_user(
            email="third@example.com", password="third_password"
        )
        initial_user_count = User.objects.count()
        response = self.client.delete(
            reverse("users:user_delete", kwargs={"pk": other_user.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), initial_user_count)


class UserTasksTest(APITestCase):

    @patch("django.utils.timezone.now")
    def test_block_inactive_users(self, mock_timezone_now):
        """Тестирование задачи блокировки неактивных пользователей."""

        test_current_time = timezone.datetime(
            2025, 7, 15, 10, 0, 0, tzinfo=timezone.get_current_timezone()
        )

        active_user_login_time = test_current_time - datetime.timedelta(days=10)
        active_user = User.objects.create_user(
            email="active_task_user@example.com", password="password1"
        )
        active_user.last_login = active_user_login_time
        active_user.save()

        inactive_user_login_time = test_current_time - datetime.timedelta(days=31)
        inactive_user = User.objects.create_user(
            email="inactive_task_user@example.com", password="password2"
        )
        inactive_user.last_login = inactive_user_login_time
        inactive_user.save()

        mock_timezone_now.return_value = test_current_time

        from users.tasks import block_inactive_users

        block_inactive_users()

        active_user.refresh_from_db()
        inactive_user.refresh_from_db()

        self.assertTrue(active_user.is_active)
        self.assertFalse(inactive_user.is_active)

        block_inactive_users()
        inactive_user.refresh_from_db()
        self.assertFalse(inactive_user.is_active)
