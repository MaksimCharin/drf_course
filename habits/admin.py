from django.contrib import admin
from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "action",
        "time",
        "place",
        "is_pleasant",
        "linked_habit",
        "periodicity",
        "reward",
        "execution_time",
        "is_public",
    )
    list_filter = ("is_pleasant", "is_public", "periodicity")
    search_fields = ("action", "place", "user__email")
    raw_id_fields = ("linked_habit",)
