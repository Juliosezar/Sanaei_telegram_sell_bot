from django.urls import path
from . import views
from .sanaie_api import ServerApi
app_name = "servers"

urlpatterns = [
    path('show_servers/', views.ShowServers.as_view(), name="show_servers"),
    path("add_server/", views.AddServer.as_view(), name="add_server"),
    path("edit_server/<int:server_id>/", views.EditServer.as_view(), name="edit_server"),
]