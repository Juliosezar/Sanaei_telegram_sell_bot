from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from sellers.models import SubSellerSubset
from accounts.models import User



class SelectSeller(LoginRequiredMixin, View):
    def get(self, request, action):
        if request.user.level_access == 1:
            sellers_list = [row.sub for row in SubSellerSubset.objects.filter(head=request.user)]
        else:
            sellers_list = [row for row in User.objects.filter(level_access__in=[0,1])]
        return render(request, "subsellers_list_configs.html", {"sellers_list": sellers_list, "action": action})


