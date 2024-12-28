from django.urls import path
from . import views

app_name = "logs"

urlpatterns = [
    path("bot_job_queue/", views.BotJobQueueLogView.as_view(), name="bot_job_queue"),
    path("sellers_job_queue/", views.SellersJobQueueLogView.as_view(), name="sellers_job_queue"),
    path("delete_job_queue/<int:id>/", views.DeleteJobQueueView.as_view(), name="delete_job_queue"),
    path("bot_status/", views.BotStatusView.as_view(), name="bot_status"),
    path("sellers_status/", views.SellersStatusView.as_view(), name="sellers_status"),
    path("bot_auto_system_log/", views.BotAutoSystemLog.as_view(), name="bot_auto_system_log"),
    path("sellers_auto_system_log/", views.SellersAutoSystemLog.as_view(), name="sellers_auto_system_log"),
]