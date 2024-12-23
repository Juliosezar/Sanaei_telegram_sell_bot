from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from configs.models import ConfigJobsQueue


class BotJobQueueLogView(LoginRequiredMixin, View):
    def get(self, request):
        data = ConfigJobsQueue.objects.filter(config__service__owner=None).order_by("-done", 'id')[:1500]
        return render(request, "job_queue.html", {"data":reversed(data)})


class DeleteJobQueueView(LoginRequiredMixin, View):
    def get(self, request, id):
        ConfigJobsQueue.objects.get(id=id).delete()
        return redirect("logs:bot_job_queue")
