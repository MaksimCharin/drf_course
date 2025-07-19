from rest_framework.serializers import ValidationError


class HabitValidator:
    def __call__(self, attrs):
        is_pleasant = attrs.get("is_pleasant")
        linked_habit = attrs.get("linked_habit")
        reward = attrs.get("reward")
        execution_time = attrs.get("execution_time")
        periodicity = attrs.get("periodicity")

        if linked_habit and reward:
            raise ValidationError(
                "Нельзя одновременно выбирать связанную привычку и указывать вознаграждение."
            )

        if is_pleasant:
            if linked_habit or reward:
                raise ValidationError(
                    "У приятной привычки не может быть вознаграждения или связанной привычки."
                )

        if linked_habit and not linked_habit.is_pleasant:
            raise ValidationError(
                "В связанные привычки могут попадать только привычки с признаком приятной привычки."
            )

        if execution_time is not None and execution_time > 120:
            raise ValidationError("Время выполнения должно быть не больше 120 секунд.")

        if periodicity is not None and (periodicity < 1 or periodicity > 7):
            raise ValidationError(
                "Периодичность выполнения привычки не может быть реже 1 раза в 7 дней."
            )

        if not is_pleasant and not (linked_habit or reward):
            raise ValidationError(
                "Полезная привычка должна иметь либо связанную привычку, либо вознаграждение."
            )
        return attrs
