from django.urls import path
from . import views

app_name = "configs"

urlpatterns = [
    path("bot_create_config/<str:form_type>/", views.BotCreateConfigView.as_view(), name="bot_create_config"),
    path("bot_list_config/", views.BotListConfigView.as_view(), name="bot_list_config"),
    path("config_page/<str:config_uuid>/", views.ConfigPage.as_view(), name="conf_page"),
    path("client_config_page/<str:config_uuid>/", views.ClientsConfigPage.as_view(), name="client_config_page"),

    path("sublink/<uuid:config_uuid>/", views.Sublink.as_view(), name="sublink"),

    path("api_get_config_time_chices/", views.ApiGetConfigTimeChoices.as_view(), name="api_get_time_choices"),
    path("api_get_config_usage_chices/", views.ApiGetConfigUsageChoices.as_view(), name="api_get_usage_choices"),
    path("api_get_config_ip_limit_chices/", views.ApiGetConfigIPLimitChoices.as_view(), name="api_get_iplimit_choices"),
    path("api_get_axact_price/", views.ApiGetConfigPriceChoices.as_view(), name="api_get_axact_price"),
]