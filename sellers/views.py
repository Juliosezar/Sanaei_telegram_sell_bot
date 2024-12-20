from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from sellers.models import SubSellerSubset
from accounts.models import User
from .forms import ChangeSellerAccessForm


class SelectSeller(LoginRequiredMixin, View):
    def get(self, request, action):
        if request.user.level_access == 1:
            sellers_list = [row.sub for row in SubSellerSubset.objects.filter(head=request.user)]
        else:
            sellers_list = [row for row in User.objects.filter(level_access__in=[0,1])]
        return render(request, "subsellers_list_configs.html", {"sellers_list": sellers_list, "action": action})



class SellersList(LoginRequiredMixin, View):
    def get(self, request):
        sellers = User.objects.filter(level_access__in=[0,1])
        return render(request, "list_sellers.html", {"sellers": sellers})

class ChangeSellerAccesses(LoginRequiredMixin, View):
    def get(self, request, seller_id):
        form = ChangeSellerAccessForm()
        return render(request,"change_seller_access.html", {"form": form})

    def post(self, request, seller_id):
        form = ChangeSellerAccessForm(request.POST)
        seller = User.objects.get(id=seller_id)
        if form.is_valid():
            cd = form.cleaned_data
            seller.level_access = cd["level_access"]
            seller.payment_limit = cd["payment_limit"] * 1000
            seller.finance_access = cd["finance_access"]
            seller.create_config_acc = cd["create_config_acc"]
            seller.list_configs_acc = cd["list_configs_acc"]
            seller.delete_config_acc = cd["delete_config_acc"]
            seller.disable_config_acc = cd["disable_config_acc"]
            seller.bot = None
            seller.save()
            return redirect("sellers:sellers_list")
        return render(request, "change_seller_access.html", {"form": form})


class AddSubSeller(LoginRequiredMixin, View):
    def get(self, request):
        pass

