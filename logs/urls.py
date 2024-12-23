from django.urls import path
from . import views

app_name = "logs"

urlpatterns = [
    path("bot_job_queue/", views.BotJobQueueLogView.as_view(), name="bot_job_queue"),
    path("delete_job_queue/<int:id>/", views.DeleteJobQueueView.as_view(), name="delete_job_queue"),
]