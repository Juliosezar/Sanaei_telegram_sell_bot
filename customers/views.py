from django.contrib import messages
from configs.models import Service
from .models import Customer
from .forms import SearchCustomerForm, ChangeWalletForm
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View


class CustomerList(LoginRequiredMixin, View):
    def get(self, request):
        customer_model = Customer.objects.all()
        form = SearchCustomerForm()
        return render(request, 'list_custumers.html', {"customer_model": reversed(customer_model), 'search_user':form})

    def post(self, request):
        form = SearchCustomerForm(request.POST)
        if form.is_valid():
            word = form.cleaned_data['search_user']
            customer_model = Customer.objects.filter(Q(chat_id__icontains=word) | Q(name__icontains=word) | Q(username__icontains=word))
            if not customer_model.exists():
                messages.error(request, "یوزری با این مشخصات یافت نشد.")
            return render(request, 'list_custumers.html', {"customer_model": reversed(customer_model),'search_user':form})
        return redirect('accounts:home')


class CustomerDetail(LoginRequiredMixin, View):
    def get(self, request, customer_id):
        customer_obj = Customer.objects.get(chat_id=customer_id)
        services = Service.objects.filter(customer=customer_obj, owner=None)
        sum_configs = services.count() or False
        return render(request, "Custumer_details.html", {"customer_obj": customer_obj, "services": services, "sum_configs": sum_configs})



class ChangeWalletAmount(LoginRequiredMixin, View):
    def get(self, request, userid):
        customer_model = Customer.objects.get(chat_id=userid)
        form = ChangeWalletForm
        return render(request, "change_wallet.html", {"form": form})

    def post(self, request, userid):
        customer_model = Customer.objects.get(chat_id=userid)
        form = ChangeWalletForm(request.POST)
        if form.is_valid():
            wallet = form.cleaned_data['wallet']
            customer_model.wallet = wallet * 1000
            customer_model.save()
            return redirect('customers:custumer_detail', userid)
        return render(request, 'change_wallet.html', {"form": form})