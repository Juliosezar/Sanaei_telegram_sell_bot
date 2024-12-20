from django.urls import path
from . import views

app_name = "sellers"

urlpatterns = [
    path("select_seller/<str:action>/", views.SelectSeller.as_view(), name="select_seller"),
    path("sellers_list/", views.SellersList.as_view(), name="sellers_list"),
    path("change_seller_access/<int:seller_id>/", views.ChangeSellerAccesses.as_view(), name="change_seller"),
    path("add_sub_seller/", views.AddSubSeller.as_view(), name="add_sub_seller"),
]