from datetime import time, timedelta
from unittest.mock import MagicMock, patch

import requests
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from habits.models import Habit
from users.models import User


class HabitAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpassword",
            telegram_chat_id="123456789",
        )
        self.client.force_authenticate(user=self.user)

        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(10, 0),
            action="Почитать перед сном",
            is_pleasant=True,
            execution_time=30,
        )

        self.useful_habit = Habit.objects.create(
            user=self.user,
            place="Улица",
            time=time(10, 0),
            action="Прогуляться",
            is_pleasant=False,
            linked_habit=self.pleasant_habit,
            execution_time=60,
        )

    def test_habit_create(self):
        data = {
            "user": self.user.pk,
            "place": "Парк",
            "time": "08:00:00",
            "action": "Пробежка",
            "is_pleasant": False,
            "reward": "Кофе",
            "periodicity": 1,
            "execution_time": 90,
            "is_public": True,
        }
        response = self.client.post(reverse("habits:habit_create"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 3)
        self.assertEqual(response.data["action"], "Пробежка")

    def test_habit_list(self):
        response = self.client.get(reverse("habits:habit_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_public_habit_list(self):
        Habit.objects.create(
            user=self.user,
            place="Офис",
            time=time(9, 0),
            action="Работа",
            is_pleasant=False,
            execution_time=120,
            is_public=True,
        )
        response = self.client.get(reverse("habits:public_habit_list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_habit_retrieve(self):
        response = self.client.get(
            reverse("habits:habit_retrieve", kwargs={"pk": self.useful_habit.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], self.useful_habit.action)

    def test_habit_update(self):
        data = {"action": "Выпить два стакана воды", "execution_time": 60}
        response = self.client.patch(
            reverse("habits:habit_update", kwargs={"pk": self.pleasant_habit.pk}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pleasant_habit.refresh_from_db()
        self.assertEqual(self.pleasant_habit.action, "Выпить два стакана воды")
        self.assertEqual(self.pleasant_habit.execution_time, 60)

    def test_habit_delete(self):
        response = self.client.delete(
            reverse("habits:habit_delete", kwargs={"pk": self.useful_habit.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Habit.objects.count(), 1)


class HabitValidationTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="validationuser@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)

        self.pleasant_habit_for_link = Habit.objects.create(
            user=self.user,
            place="Кухня",
            time=time(10, 10),
            action="Сделать легкий перекус",
            is_pleasant=True,
            execution_time=30,
        )

    def test_linked_habit_is_pleasant(self):
        non_pleasant_habit_for_link = Habit.objects.create(
            user=self.user,
            place="Дом",
            time=time(11, 0),
            action="Позвонить другу",
            is_pleasant=False,
            execution_time=30,
        )
        data = {
            "user": self.user.pk,
            "place": "Офис",
            "time": "09:00:00",
            "action": "Закончить отчет",
            "is_pleasant": False,
            "linked_habit": non_pleasant_habit_for_link.pk,
            "execution_time": 90,
        }
        response = self.client.post(reverse("habits:habit_create"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "В связанные привычки могут попадать только привычки с признаком приятной привычки.",
        )

    def test_linked_habit_or_reward_only_one(self):
        data = {
            "user": self.user.pk,
            "place": "Дом",
            "time": "20:00:00",
            "action": "Посмотреть фильм",
            "is_pleasant": False,
            "reward": "Съесть попкорн",
            "linked_habit": self.pleasant_habit_for_link.pk,
            "execution_time": 60,
        }
        response = self.client.post(reverse("habits:habit_create"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "Нельзя одновременно выбирать связанную привычку и указывать вознаграждение.",
        )

    def test_pleasant_habit_no_reward_or_linked(self):
        data = {
            "user": self.user.pk,
            "place": "Дом",
            "time": "07:00:00",
            "action": "Послушать музыку",
            "is_pleasant": True,
            "reward": "Шоколад",
            "execution_time": 30,
        }
        response = self.client.post(reverse("habits:habit_create"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "У приятной привычки не может быть вознаграждения или связанной привычки.",
        )

    def test_execution_time_limit(self):
        data = {
            "user": self.user.pk,
            "place": "Дом",
            "time": "07:00:00",
            "action": "Сделать зарядку",
            "is_pleasant": False,
            "reward": "Позавтракать",
            "execution_time": 121,
        }
        response = self.client.post(reverse("habits:habit_create"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertEqual(
            str(response.data["non_field_errors"][0]),
            "Время выполнения должно быть не больше 120 секунд.",
        )

    def test_periodicity_limit(self):
        data = {
            "user": self.user.pk,
            "place": "Дом",
            "time": "07:00:00",
            "action": "Позвонить маме",
            "is_pleasant": False,
            "reward": "Съесть конфету",
            "periodicity": 8,
            "execution_time": 60,
        }
        response = self.client.post(reverse("habits:habit_create"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("periodicity", response.data)
        self.assertEqual(
            str(response.data["periodicity"][0]), '"8" is not a valid choice.'
        )


class HabitTasksTest(APITestCase):

    def setUp(self):
        self.user_telegram = User.objects.create_user(
            email="telegram_user@example.com",
            password="testpassword",
            telegram_chat_id="123456789",
        )
        self.user_no_telegram = User.objects.create_user(
            email="no_telegram_user@example.com",
            password="testpassword",
            telegram_chat_id=None,
        )

        self.test_start_time = timezone.localtime(timezone.now()).replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        self.pleasant_habit_for_linked = Habit.objects.create(
            user=self.user_telegram,
            place="Кухня",
            time=time(10, 10),
            action="Сделать легкий перекус",
            is_pleasant=True,
            execution_time=30,
        )

        self.habit_to_remind = Habit.objects.create(
            user=self.user_telegram,
            place="Дом",
            time=time(10, 0),
            action="Почитать перед сном",
            is_pleasant=False,
            reward="Выпить воды",
            periodicity=1,
            execution_time=30,
            last_reminder_sent=self.test_start_time - timedelta(days=1),
        )

        self.habit_with_linked_to_remind = Habit.objects.create(
            user=self.user_telegram,
            place="Улица",
            time=time(10, 0),
            action="Прогуляться",
            is_pleasant=False,
            linked_habit=self.pleasant_habit_for_linked,
            periodicity=1,
            execution_time=60,
            last_reminder_sent=self.test_start_time - timedelta(days=1),
        )

        self.habit_no_chat_id = Habit.objects.create(
            user=self.user_no_telegram,
            place="Работа",
            time=time(10, 0),
            action="Закрыть отчет",
            is_pleasant=False,
            reward="Кофе",
            periodicity=1,
            execution_time=90,
            last_reminder_sent=self.test_start_time - timedelta(days=1),
        )

        self.habit_already_sent_today = Habit.objects.create(
            user=self.user_telegram,
            place="Спальня",
            time=time(10, 0),
            action="Заправить кровать",
            is_pleasant=False,
            reward="Завтрак",
            periodicity=1,
            execution_time=15,
            last_reminder_sent=self.test_start_time,
        )

    @patch("habits.tasks.requests.post")
    @patch("django.utils.timezone.localtime")
    def test_check_and_send_reminders(self, mock_localtime, mock_requests_post):
        mock_localtime.return_value = self.test_start_time

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
        mock_requests_post.return_value = mock_response

        from habits.tasks import check_and_send_reminders

        check_and_send_reminders()

        self.assertEqual(mock_requests_post.call_count, 3)

    @patch("habits.tasks.send_telegram_message")
    @patch("django.utils.timezone.localtime")
    def test_check_and_send_reminders_already_sent_today(
        self, mock_localtime, mock_send_telegram_message
    ):
        mock_localtime.return_value = self.test_start_time

        self.habit_already_sent_today.last_reminder_sent = self.test_start_time
        self.habit_already_sent_today.save()

        from habits.tasks import check_and_send_reminders

        check_and_send_reminders()

        self.habit_already_sent_today.refresh_from_db()
        self.assertEqual(
            self.habit_already_sent_today.last_reminder_sent.date(),
            self.test_start_time.date(),
        )

    @patch("habits.tasks.send_telegram_message")
    @patch("django.utils.timezone.localtime")
    def test_check_and_send_reminders_no_chat_id(
        self, mock_localtime, mock_send_telegram_message
    ):
        mock_localtime.return_value = self.test_start_time

        self.user_no_telegram.telegram_chat_id = None
        self.user_no_telegram.save()

        from habits.tasks import check_and_send_reminders

        check_and_send_reminders()

        self.habit_no_chat_id.refresh_from_db()
        self.assertEqual(
            self.habit_no_chat_id.last_reminder_sent,
            self.test_start_time - timedelta(days=1),
        )

    @patch("habits.tasks.requests.post")
    @patch("django.utils.timezone.localtime")
    def test_check_and_send_reminders_telegram_api_failure(
        self, mock_localtime, mock_requests_post
    ):
        mock_localtime.return_value = self.test_start_time

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Telegram API Error"
        )
        mock_requests_post.return_value = mock_response

        from habits.tasks import check_and_send_reminders

        check_and_send_reminders()

        self.assertEqual(mock_requests_post.call_count, 3)

        self.habit_to_remind.refresh_from_db()
        self.habit_with_linked_to_remind.refresh_from_db()
        self.assertEqual(
            self.habit_to_remind.last_reminder_sent,
            self.test_start_time - timedelta(days=1),
        )
        self.assertEqual(
            self.habit_with_linked_to_remind.last_reminder_sent,
            self.test_start_time - timedelta(days=1),
        )
