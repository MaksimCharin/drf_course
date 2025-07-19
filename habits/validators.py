from rest_framework.serializers import ValidationError

from habits.models import Habit


class HabitValidator:
    def __call__(self, attrs):
        is_update = False
        instance = None
        if hasattr(self, "instance") and self.instance:
            instance = self.instance
            is_update = True

        is_pleasant = attrs.get("is_pleasant")
        linked_habit = attrs.get("linked_habit")
        reward = attrs.get("reward")
        execution_time = attrs.get("execution_time")
        periodicity = attrs.get("periodicity")

        if is_update:
            if is_pleasant is None:
                is_pleasant = instance.is_pleasant
            if linked_habit is None:
                linked_habit = instance.linked_habit
            if reward is None:
                reward = instance.reward
            if execution_time is None:
                execution_time = instance.execution_time
            if periodicity is None:
                periodicity = instance.periodicity

        if linked_habit and reward:
            raise ValidationError(
                "Нельзя одновременно выбирать связанную привычку и указывать вознаграждение."
            )

        if is_pleasant:
            if linked_habit or reward:
                raise ValidationError(
                    "У приятной привычки не может быть вознаграждения или связанной привычки."
                )
        else:
            if not (linked_habit or reward):
                raise ValidationError(
                    "Полезная привычка должна иметь либо связанную привычку, либо вознаграждение."
                )

        if linked_habit:
            if isinstance(linked_habit, int):
                try:
                    linked_habit_obj = Habit.objects.get(pk=linked_habit)
                except Habit.DoesNotExist:
                    raise ValidationError("Связанная привычка не найдена.")
            else:
                linked_habit_obj = linked_habit

            if not linked_habit_obj.is_pleasant:
                raise ValidationError(
                    "В связанные привычки могут попадать только привычки с признаком приятной привычки."
                )

        if execution_time is not None and execution_time > 120:
            raise ValidationError("Время выполнения должно быть не больше 120 секунд.")

        if periodicity is not None and (periodicity < 1 or periodicity > 7):
            raise ValidationError(
                "Периодичность выполнения привычки не может быть реже 1 раза в 7 дней."
            )

        return attrs
