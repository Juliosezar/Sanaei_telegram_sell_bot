from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path("home/bot/", views.HomeBotView.as_view(), name='home_bot'),
    path("home/Sellers/", views.HomeSellersView.as_view(), name='home_sellers'),
]