from django.contrib import messages
from django.shortcuts import render
from .models import Customer
from .forms import SearchCustomerForm
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from rest_framework.response import Response
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
