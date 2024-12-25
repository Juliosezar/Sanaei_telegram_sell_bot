from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from configs.models import ConfigJobsQueue
from servers.models import Server
from .models import CeleryLog
from datetime import datetime
from sellers.models import SubSellerSubset

class LogAction:
    @staticmethod
    def create_celery_log(owner, desc):
        CeleryLog.objects.create(
            owner=owner,
            description=desc,
            timestamp=datetime.now().timestamp()
        ).save()



class BotJobQueueLogView(LoginRequiredMixin, View):
    def get(self, request):
        data = ConfigJobsQueue.objects.filter(config__service__owner=None).order_by("-done", 'id')[:1500]
        return render(request, "bot_job_queue.html", {"data":reversed(data)})

class SellersJobQueueLogView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.level_access == 10:
            data = ConfigJobsQueue.objects.filter(~Q(config__service__owner=None)).order_by("-done", 'id')[:1500]
        elif request.user.level_access == 1:
            sellers = [request.user]
            for seller in SubSellerSubset.objects.filter(head=request.user):
                sellers.append(seller.sub)
            data = ConfigJobsQueue.objects.filter(config__service__owner__in=sellers).order_by("-done", 'id')[:1500]
        else:
            data = ConfigJobsQueue.objects.filter(config__service__owner=request.user).order_by("-done", 'id')[:1500]

        return render(request, "sellers_job_queue.html", {"data":reversed(data)})


class DeleteJobQueueView(LoginRequiredMixin, View):
    def get(self, request, id):
        ConfigJobsQueue.objects.get(id=id).delete()
        return redirect("logs:bot_job_queue")


class BotStatusView(LoginRequiredMixin, View):
    def get(self, request):
        servers = Server.objects.all()
        return render(request, "bot_status.html", {"servers":servers})


class SellersStatusView(LoginRequiredMixin, View):
    def get(self, request):
        servers = Server.objects.all()
        return render(request, "sellers_status.html", {"servers": servers})

