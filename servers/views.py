from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from .models import Server
from django.views import View
from .forms import AddServerForm, EditServerForm
import re



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
            regex = r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}"
            config_text:str = cd["config_example"].split("#")[0] + "#"
            matches = re.search(regex, config_text)
            print(type(matches.group()))
            Server.objects.create(
                id=cd["ID"],
                name=cd["server_name"],
                url=cd["server_url"],
                username=cd["username"],
                password=cd["password"],
                inbound_id=cd["inbound_id"],
                active=cd["active"],
                maximum_connection=cd["maximum_connection"],
                config_example=config_text.replace(matches.group(), "uuid"),
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
            regex = r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}"
            cd = form.cleaned_data
            config_example = (cd["config_example"].split("#")[0]) + "#"
            if not "uuid" in config_example:
                matches = re.search(regex, config_example)
                config_example = config_example.replace(matches.group(), "uuid")

            obj = Server.objects.get(id=server_id)
            obj.name = cd["server_name"]
            obj.url = cd["server_url"]
            obj.username = cd["username"]
            obj.password = cd["password"]
            obj.inbound_id = cd["inbound_id"]
            obj.active = cd["active"]
            obj.maximum_connection = cd["maximum_connection"]
            obj.config_example = config_example
            obj.save()
            return redirect('servers:show_servers')
        return render(request, "add_server.html", {'form': form, "edit": True})


