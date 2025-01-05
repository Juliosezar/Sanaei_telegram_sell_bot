from django.urls import path
from . import views

app_name = "configs"


urlpatterns = [
    path("bot_create_config/<str:form_type>/", views.BotCreateConfigView.as_view(), name="bot_create_config"),
    path("bot_renew_config/<uuid:config_uuid>/<str:form_type>/", views.BotRenewConfigView.as_view(), name="bot_renew_config"),
    path("bot_change_config/<uuid:config_uuid>/", views.BotChangeConfigPage.as_view(), name="bot_change_config"),
    path("bot_list_config/<int:page>/", views.BotListConfigView.as_view(), name="bot_list_config"),
    path("config_page/<str:config_uuid>/", views.ConfigPage.as_view(), name="conf_page"),
    path("client_config_page/<str:config_uuid>/", views.ClientsConfigPage.as_view(), name="client_config_page"),
    path('delete_config/<str:config_uuid>/',views.DeleteConfig.as_view(), name="delete_config"),
    path('disable_config/<str:config_uuid>/<int:enable>/',views.DisableConfig.as_view(), name="disable_config"),

    path("api_get_config_time_chices/", views.ApiGetConfigTimeChoices.as_view(), name="api_get_time_choices"),
    path("api_get_config_usage_chices/", views.ApiGetConfigUsageChoices.as_view(), name="api_get_usage_choices"),
    path("api_get_config_ip_limit_chices/", views.ApiGetConfigIPLimitChoices.as_view(), name="api_get_iplimit_choices"),
    path("api_get_axact_price/", views.ApiGetConfigPriceChoices.as_view(), name="api_get_axact_price"),


    path("sublink/<uuid:config_uuid>/", views.Sublink.as_view(), name="sublink"),

    path("sellers/create/<str:username>/<str:form_type>/", views.SellersCreateConfigView.as_view(),name="seller_create"),
    path("sellers/list/<str:username>/", views.SellersListConfigView.as_view(),name="seller_list"),
    path("sellers/change_config/<uuid:config_uuid>/", views.SellersChangeConfigPage.as_view(), name="sellers_change_config"),
    path("sellers_config_page/<str:config_uuid>/", views.SellersConfigPage.as_view(), name="sellers_conf_page"),
    path("sellers_renew_page/<str:config_uuid>/<str:form_type>/", views.SellersRenewConfigView.as_view(), name="sellers_renew"),
    path("sellers/disable_all_services/", views.DisableAllService.as_view(), name="sellers_disable_all_services"),


    path("sellers_api_get_config_time_chices/", views.ApiSellersGetConfigTimeChoices.as_view(), name="seller_api_get_time_choices"),
    path("sellers_api_get_config_usage_chices/", views.ApiSellersGetConfigUsageChoices.as_view(), name="seller_api_get_usage_choices"),
    path("sellers_api_get_config_ip_limit_chices/", views.ApiSellersGetConfigIPLimitChoices.as_view(), name="seller_api_get_iplimit_choices"),
    path("sellers_api_get_axact_price/", views.ApiSellersGetConfigPriceChoices.as_view(), name="seller_api_get_axact_price"),

]




