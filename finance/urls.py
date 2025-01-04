from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path('confirm_payment/<int:show_box>/', views.ConfirmPaymentPage.as_view(), name='confirm_payments'),
    path('first_confirm_payment/<int:obj_id>/', views.FirstConfirmPayment.as_view(), name='first_confirm'),
    path('secoend_confirm_payment/<int:obj_id>/', views.SecondConfirmPayment.as_view(), name='second_confirm'),
    path('deny_payment/<int:obj_id>/', views.DenyPaymentPage.as_view(), name='deny_payments'),
    path('edit_price_payment/<int:obj_id>/<str:typ>/', views.EditPricePayment.as_view(), name='edit_price'),
    path("pay_debts/<uuid:uuid>/<int:action>/", views.PayDebts.as_view(), name='pay_debts'),

    path('show_prices/', views.ShowPrices.as_view(), name='show_prices'),
    path('delete_or_edit_price/<int:obj_id>/<str:action>/', views.DeleteOrEditPrice.as_view(),
         name='delete_or_edit_price'),
    path('add_price/', views.AddPrice.as_view(), name='add_price'),

    path("sellers_sum_bils/", views.SellersSumBills.as_view(), name='sellers_sum_bils'),
    path("sellers_pay_bill/<str:username>/", views.SellerPayBills.as_view(), name='sellers_pay_bill'),
    path("sellers_delete_pay_bill/<int:id>/", views.SellerDeletePayBills.as_view(), name='sellers_delete_pay_bill'),
    path("select_seller/<str:action>/", views.SelectSeller.as_view(), name='select_seller'),
    path("sellers_show_prices/<str:username>/",views.SellersShowPrices.as_view(), name='sellers_show_prices' ),
    path('seller_delete/<int:obj_id>/', views.SellersDeletePrice.as_view(), name='seller_delete_price'),
    path('seller_add_price/<str:username>/', views.SellersAddPrice.as_view(), name='seller_add_price'),

    path("show_off_codes/", views.ShowOffCodes.as_view(), name='show_off_codes'),
    path("add_off_codes/", views.AddOffCode.as_view(), name='add_off_codes'),
    path("delete_off_code/<str:uuid>/", views.DeleteOffCode.as_view(), name='delete_off_code'),
]