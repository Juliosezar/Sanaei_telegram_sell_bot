from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, AddUserForm
from .models import User
import json
from django.conf import settings


# Create your views here.
class LoginView(View):
    formclass = LoginForm

    def get(self, request):
        form = self.formclass
        return render(request, "log_in.html", {"form": form})

    def post(self, request):
        form = self.formclass(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd["username"], password=cd["password"])
            if user is not None:
                login(request, user)
                return redirect("accounts:home_bot")
        return render(request, "log_in.html", {"form": form})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.error(request, "شما از حساب کاربری خود خارج شدید.")
        return redirect("accounts:login")


class RegisterView(LoginRequiredMixin, View):
    form = AddUserForm

    def get(self, request):
        form = self.form
        return render(request, "register_user.html", {"form": form})

    def post(self, request):
        form = self.form(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = User(username=cd["username"], level_access=0, is_active=True)
            user.set_password(cd["password"])
            user.save()
            return redirect("accounts:home_bot")
        return render(request, "register_user.html", {"form": form})


class HomeBotView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.level_access != 10:
                return redirect("accounts:home_sellers")
        else:
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        # search_user = SearchUserForm()
        # search_config = SearchConfigForm()
        # for i in Server.objects.all():
        #     if ((now_timestamp() - i.last_update) // 60) > 30:
        #         messages.error(request, f"مشکل اتصال به سرور {i.name}")
        return render(request, "home_bot.html", )


class HomeSellersView(LoginRequiredMixin, View):
    def get(self, request):
        # search_config = SearchConfigForm()
        # for i in Server.objects.all():
        #     if ((now_timestamp() - i.last_update) // 60) > 30:
        #         messages.error(request, f"مشکل اتصال به سرور {i.name}")
        return render(request, "home_sellers.html", )


# class SettingsPage(LoginRequiredMixin, View):
#     def get(self, request):
#         form = ChangeSettingForm()
#         return render(request, "settings.html", {"form": form})
#
#     def post(self, request):
#         form = ChangeSettingForm(request.POST)
#         if form.is_valid():
#             cd = form.cleaned_data
#             with open("settings.json", "r+") as f:
#                 datas = json.load(f)
#                 datas["pay_card_number"] = cd["card_number"]
#                 datas["pay_card_name"] = cd["card_name"]
#                 datas["prices_msg_id"] = cd["prices_msg_id"]
#                 datas["unlimit_limit"]["1u"]["1m"] = cd["U1_1M"]
#                 datas["unlimit_limit"]["1u"]["2m"] = cd["U1_2M"]
#                 datas["unlimit_limit"]["1u"]["3m"] = cd["U1_3M"]
#                 datas["unlimit_limit"]["2u"]["1m"] = cd["U2_1M"]
#                 datas["unlimit_limit"]["2u"]["2m"] = cd["U2_2M"]
#                 datas["unlimit_limit"]["2u"]["3m"] = cd["U2_3M"]
#                 datas["config_name_counter"] = cd["config_name_counter"]
#                 f.seek(0)
#                 json.dump(datas, f, indent=4)
#                 f.truncate()
#             return redirect("accounts:home_bot")
#         return render(request, "settings.html", {"form": form})

