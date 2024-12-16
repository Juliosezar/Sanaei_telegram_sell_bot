from django.urls import path
from . import views

app_name = "sellers"

urlpatterns = [
    path("select_seller/<str:action>/", views.SelectSeller.as_view(), name="select_seller"),
]