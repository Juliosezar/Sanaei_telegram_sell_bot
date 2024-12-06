from django.urls import path
from . import views

app_name = "configs"

urlpatterns = [
    path("bot_create_config/<int:type_>/", views.BotCreateConfigView.as_view(), name="bot_create_config"),
    path("bot_list_config/", views.BotListConfigView.as_view(), name="bot_list_config"),
]