from django.db import models
from django.conf import settings


class Habit(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="habits",
    )
    place = models.CharField(max_length=255, verbose_name="Место")
    time = models.TimeField(verbose_name="Время выполнения")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_pleasant = models.BooleanField(
        default=False, verbose_name="Признак приятной привычки"
    )
    linked_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанная привычка",
        help_text="Привычка, которая связана с другой привычкой, "
                  "важно указывать для полезных привычек, "
                  "но не для приятных.",
    )
    periodicity_choices = [
        (1, "Ежедневно"),
        (2, "Раз в 2 дня"),
        (3, "Раз в 3 дня"),
        (4, "Раз в 4 дня"),
        (5, "Раз в 5 дней"),
        (6, "Раз в 6 дней"),
        (7, "Раз в 7 дней"),
    ]
    periodicity = models.PositiveSmallIntegerField(
        choices=periodicity_choices,
        default=1,
        verbose_name="Периодичность",
        help_text="Периодичность выполнения привычки (в днях, не реже 1 раза в 7 дней).",
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Вознаграждение",
        help_text="Чем пользователь должен себя вознаградить после выполнения.",
    )
    execution_time = models.PositiveSmallIntegerField(
        verbose_name="Время на выполнение (секунды)",
        help_text="Время, которое предположительно потратит пользователь "
                  "на выполнение привычки (не более 120 секунд).",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Признак публичности",
        help_text="Привычки можно публиковать в общий доступ, "
                  "чтобы другие пользователи могли брать "
                  "в пример чужие привычки.",
    )

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["time"]

    def __str__(self):
        return f"Я буду {self.action} в {self.time} в {self.place} ({self.user.email})"
