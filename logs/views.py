from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from configs.models import ConfigJobsQueue
from servers.models import Server
from .models import CeleryLog
from datetime import datetime
from sellers.models import SubSellerSubset
from bot.models import SendMessage


class LogAction:
    @staticmethod
    def create_celery_log(owner, desc, customer, tag):
        CeleryLog.objects.create(
            customer=customer,
            owner=owner,
            description=desc,
            timestamp=datetime.now().timestamp(),
            tag=tag,
        ).save()



class BotJobQueueLogView(LoginRequiredMixin, View):
    def get(self, request):
        data = ConfigJobsQueue.objects.filter(config__service__owner=None).order_by("done", '-id')[:1500]
        return render(request, "bot_job_queue.html", {"data":data})

class SellersJobQueueLogView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.level_access == 10:
            data = ConfigJobsQueue.objects.filter(~Q(config__service__owner=None)).order_by("done", '-id')[:1500]
        elif request.user.level_access == 1:
            sellers = [request.user]
            for seller in SubSellerSubset.objects.filter(head=request.user):
                sellers.append(seller.sub)
            data = ConfigJobsQueue.objects.filter(config__service__owner__in=sellers).order_by("done", '-id')[:1500]
        else:
            data = ConfigJobsQueue.objects.filter(config__service__owner=request.user).order_by("done", '-id')[:1500]

        return render(request, "sellers_job_queue.html", {"data":data})


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


class BotAutoSystemLog(LoginRequiredMixin, View):
    def get(self, request):
        logs = CeleryLog.objects.filter(owner=None).order_by("-id")[:1500]
        return render(request, "bot_auto_system_log.html", {"logs": logs})


class SellersAutoSystemLog(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.level_access == 10:
            logs = CeleryLog.objects.filter(~Q(owner=None)).order_by('-id')[:1500]
        elif request.user.level_access == 1:
            sellers = [request.user]
            for seller in SubSellerSubset.objects.filter(head=request.user):
                sellers.append(seller.sub)
            logs = CeleryLog.objects.filter(owner__in=sellers).order_by('-id')[:1500]
        else:
            logs = CeleryLog.objects.filter(owner=request.user).order_by('-id')[:1500]


        return render(request, "sellers_auto_system_log.html", {"logs": logs})


class SendMsgsLogsView(LoginRequiredMixin, View):
    def get(self, request):
        logs = SendMessage.objects.all().order_by("-created_at")[:1000]
        return render(request, "messages_logs.html", {"logs": logs})


class DeleteMsgView(LoginRequiredMixin, View):
    def get(self, request, typ):
        if typ == "Succes":
            SendMessage.objects.filter(done=True).delete()
        elif typ == "Failure":
            SendMessage.objects.filter(done=False, try_count=3).delete()
        return redirect("logs:send_msgs_log")