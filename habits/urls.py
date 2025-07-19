from django.urls import path
from habits.views import (
    HabitListAPIView,
    HabitPublicListAPIView,
    HabitCreateAPIView,
    HabitRetrieveAPIView,
    HabitUpdateAPIView,
    HabitDestroyAPIView,
)
from habits.apps import HabitsConfig

app_name = HabitsConfig.name

urlpatterns = [
    path("", HabitListAPIView.as_view(), name="habit_list"),
    path("public/", HabitPublicListAPIView.as_view(), name="public_habit_list"),
    path("create/", HabitCreateAPIView.as_view(), name="habit_create"),
    path("<int:pk>/", HabitRetrieveAPIView.as_view(), name="habit_retrieve"),
    path("<int:pk>/update/", HabitUpdateAPIView.as_view(), name="habit_update"),
    path("<int:pk>/delete/", HabitDestroyAPIView.as_view(), name="habit_delete"),
]
