import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Server
from django.views import View
from .forms import AddServerForm, EditServerForm
from binary import BinaryUnits, convert_units
import datetime
import requests
from .sanaie_api import ServerApi



class ShowServers(LoginRequiredMixin, View):
    def get(self, request):
        obj = Server.objects.all()
        return render(request, "show_servers.html", {'servers': obj})


class AddServer(LoginRequiredMixin, View):
    def get(self, request):
        form = AddServerForm()
        return render(request, "add_server.html", {'form': form})

    def post(self, request):
        form = AddServerForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            Server.objects.create(
                ID=cd["ID"],
                name=cd["server_name"],
                url=cd["server_url"],
                username=cd["username"],
                password=cd["password"],
                fake_domain=cd["server_fake_domain"],
                inbound_id=cd["inbound_id"],
                inbound_port=cd["inbound_port"],
                active=cd["active"],
                maximum_connection=cd["maximum_connection"]
            ).save()
            return redirect('servers:show_servers')
        return render(request, "add_server.html", {'form': form})


class EditServer(LoginRequiredMixin, View):
    def get(self, request, server_id):
        form = EditServerForm(server_id=server_id)
        return render(request, "add_server.html", {'form': form})

    def post(self, request, server_id):
        form = EditServerForm(request.POST, server_id=server_id)
        if form.is_valid():
            cd = form.cleaned_data
            obj = Server.objects.get(ID=server_id)
            obj.name = cd["server_name"]
            obj.url = cd["server_url"]
            obj.username = cd["username"]
            obj.password = cd["password"]
            obj.fake_domain = cd["server_fake_domain"]
            obj.inbound_id = cd["inbound_id"]
            obj.inbound_port = cd["inbound_port"]
            obj.active = cd["active"]
            obj.maximum_connection = cd["maximum_connection"]
            obj.save()
            return redirect('servers:show_servers')
        return render(request, "add_server.html", {'form': form, "edit": True})


