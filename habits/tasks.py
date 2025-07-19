from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from habits.models import Habit
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_telegram_message(chat_id, message):
    """Отправляет сообщение в Telegram"""
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logger.info(f"Сообщение успешно отправлено в Telegram для chat_id {chat_id}: {message}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram для chat_id {chat_id}: {e}")
        return {"error": str(e)}

@shared_task
def check_and_send_reminders():
    """Проверяет привычки и отправляет напоминания в Telegram"""
    now = timezone.localtime(timezone.now())
    current_time = now.time()
    current_weekday = now.weekday()

    habits = Habit.objects.filter(user__is_active=True).select_related('user', 'linked_habit')

    for habit in habits:
        if current_weekday % habit.periodicity != 0:
            continue

        habit_time = habit.time
        if current_time.hour == habit_time.hour and current_time.minute == habit_time.minute:
            user_chat_id = habit.user.telegram_chat_id
            if user_chat_id:
                message = (
                    f"👋 Напоминание о привычке: <b>{habit.action}</b>\n"
                    f"⏰ Время: {habit.time.strftime('%H:%M')}\n"
                    f"📍 Место: {habit.place}\n"
                )
                if habit.reward:
                    message += f"🎁 Вознаграждение: {habit.reward}\n"
                elif habit.linked_habit:
                    message += (
                        f"✨ После выполнения сделайте: <b>{habit.linked_habit.action}</b>\n"
                        f"(Приятная привычка: в {habit.linked_habit.time.strftime('%H:%M')} в {habit.linked_habit.place})\n"
                    )

                send_telegram_message.delay(user_chat_id, message)
                logger.info(f"Запланирована отправка напоминания для привычки '{habit.action}' пользователю {habit.user.email}")
            else:
                logger.warning(f"У пользователя {habit.user.email} нет Telegram Chat ID для привычки '{habit.action}'. Напоминание не отправлено.")