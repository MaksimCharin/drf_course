from rest_framework import serializers

from habits.models import Habit
from habits.validators import HabitValidator


class HabitSerializer(serializers.ModelSerializer):
    linked_habit_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Habit
        fields = "__all__"

    def validate(self, attrs):
        validator = HabitValidator()
        if self.instance:
            validator.instance = self.instance
        validator(attrs)
        return attrs

    def get_linked_habit_data(self, obj):
        """Возвращает упрощенные данные связанной привычки для отображения"""
        if obj.linked_habit:
            return {
                "id": obj.linked_habit.id,
                "action": obj.linked_habit.action,
                "place": obj.linked_habit.place,
                "time": obj.linked_habit.time.strftime("%H:%M:%S"),
                "is_pleasant": obj.linked_habit.is_pleasant,
            }
        return None
