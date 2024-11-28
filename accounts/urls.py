from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path("Home/bot/", views.HomeBotView.as_view(), name='home_bot'),
    path("Home/Sellers/", views.HomeSellersView.as_view(), name='home_sellers'),
]