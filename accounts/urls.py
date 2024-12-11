from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path("home/bot/", views.HomeBotView.as_view(), name='home_bot'),
    path("home/Sellers/", views.HomeSellersView.as_view(), name='home_sellers'),

    path("settings/", views.SettingsPage.as_view(), name='settings'),
    path("vpn_apps/", views.VpnAppsPage.as_view(), name='vpn_apps'),
    path("delete_app/<int:ind>/", views.DeleteAppPage.as_view(), name='delete_app'),
    path("add_vpn_app/", views.AddAppPage.as_view(), name='add_vpn_app'),
]