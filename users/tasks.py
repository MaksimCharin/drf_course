from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from users.models import User


@shared_task
def block_inactive_users():
    one_month_ago = timezone.now() - timedelta(days=30)
    inactive_users = User.objects.filter(last_login__lt=one_month_ago, is_active=True)

    if inactive_users.exists():
        count = inactive_users.update(is_active=False)
        print(f"Заблокировано {count} неактивных пользователей.")
    else:
        print("Неактивных пользователей для блокировки не найдено.")
