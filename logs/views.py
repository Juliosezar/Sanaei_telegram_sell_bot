from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from configs.models import ConfigJobsQueue, Service
from customers.models import Customer
from finance.models import PurchaseRecord, BotPayment
from servers.models import Server
from .models import CeleryLog
from datetime import datetime
from sellers.models import SubSellerSubset
from bot.models import SendMessage
from django.db.models import F, Sum
from rest_framework.views import APIView
from rest_framework.response import Response


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
        return redirect(request.META.get('HTTP_REFERER', '/'))


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
        logs = CeleryLog.objects.filter(owner=None).order_by("-id")[:1000]
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



class ReportsAll(View, LoginRequiredMixin):
    def get(self, request):
        now = int(datetime.now().timestamp())
        one_month_ago_time = now - 2629800
        one_day_ago_time = now - 86400
        one_week_ago_time = now - 604800


        configs_count = Service.objects.all().count()
        active_configs_count = Service.objects.filter(status=0).count()
        ended_configs_count = Service.objects.filter(status=2).count()
        disable_configs_count = Service.objects.filter(status=1).count()
        infinitconfs_count = Service.objects.filter(usage_limit=0).count()
        infinit_time_confs_count = Service.objects.filter(expire_time=0).count()

        buys_count_all_time = PurchaseRecord.objects.filter(type=0).count()
        tamdids_count_all_time = PurchaseRecord.objects.filter(type=1).count()
        perches_all_count_all_time = buys_count_all_time + tamdids_count_all_time
        buys_price_all_time = PurchaseRecord.objects.filter(type=0).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_all_time = PurchaseRecord.objects.filter(type=1).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_all_time = buys_price_all_time + tamdids_price_all_time
        deny_pays_count_all_time = BotPayment.objects.filter(status=9).count()

        buys_count_last_month = PurchaseRecord.objects.filter(type=0,date_time__range=(one_month_ago_time,now)).count()
        tamdids_count_last_month = PurchaseRecord.objects.filter(type=1,date_time__range=(one_month_ago_time,now)).count()
        perches_count_last_month = buys_count_last_month + tamdids_count_last_month
        buys_price_last_month = PurchaseRecord.objects.filter(type=0,date_time__range=(one_month_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_month = PurchaseRecord.objects.filter(type=1,date_time__range=(one_month_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_month = tamdids_price_last_month + buys_price_last_month

        buys_count_last_week = PurchaseRecord.objects.filter(type=0,date_time__range=(one_week_ago_time,now)).count()
        tamdids_count_last_week = PurchaseRecord.objects.filter(type=1,date_time__range=(one_week_ago_time,now)).count()
        perches_count_last_week = buys_count_last_week + tamdids_count_last_week
        buys_price_last_week = PurchaseRecord.objects.filter(type=0,date_time__range=(one_week_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_week = PurchaseRecord.objects.filter(type=1,date_time__range=(one_week_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_week = buys_price_last_week + tamdids_price_last_week

        buys_count_last_day = PurchaseRecord.objects.filter(type=0,date_time__range=(one_day_ago_time,now)).count()
        tamdids_count_last_day = PurchaseRecord.objects.filter(type=1,date_time__range=(one_day_ago_time,now)).count()
        perches_count_last_day = buys_count_last_day + tamdids_count_last_day
        buys_price_last_day = PurchaseRecord.objects.filter(type=0,date_time__range=(one_day_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_day = PurchaseRecord.objects.filter(type=1,date_time__range=(one_day_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_day = buys_price_last_day + tamdids_price_last_day

        data = { "configs_count": configs_count,"active_configs_count": active_configs_count,"ended_configs_count": ended_configs_count,
                 "disable_configs_count": disable_configs_count, "infinitconfs_count": infinitconfs_count,
                 "infinit_time_confs_count": infinit_time_confs_count, "perches_all_count_all_time": perches_all_count_all_time,
                 "buys_count_all_time": buys_count_all_time, "tamdids_count_all_time": tamdids_count_all_time,
                 "perches_price_all_time": perches_price_all_time, "buys_price_all_time": buys_price_all_time,
                 "tamdids_price_all_time": tamdids_price_all_time,
                 "perches_count_last_month": perches_count_last_month,"buys_count_last_month": buys_count_last_month,
                 "tamdids_count_last_month": tamdids_count_last_month,"buys_price_last_month":buys_price_last_month,
                 "perches_price_last_month": perches_price_last_month, "tamdids_price_last_month":tamdids_price_last_month,
                 "buys_count_last_week":buys_count_last_week, "buys_count_last_day":buys_count_last_day,
                     "tamdids_count_last_week":tamdids_count_last_week, "tamdids_count_last_day":tamdids_count_last_day,
                 "perches_count_last_week":perches_count_last_week, "perches_count_last_day":perches_count_last_day,
                     "buys_price_last_week":buys_price_last_week, "buys_price_last_day":buys_price_last_day,
                 "tamdids_price_last_week":tamdids_price_last_week, "tamdids_price_last_day":tamdids_price_last_day,
                     "perches_price_last_week":perches_price_last_week, "perches_price_last_day":perches_price_last_day,
        }
        return render(request, "reports.html", data)


class ReportsBot(View, LoginRequiredMixin):
    def get(self, request):
        now = int(datetime.now().timestamp())
        one_month_ago_time = now - 2629800
        one_day_ago_time = now - 86400
        one_week_ago_time = now - 604800


        configs_count = Service.objects.filter(owner=None).count()
        active_configs_count = Service.objects.filter(status=0,owner=None).count()
        ended_configs_count = Service.objects.filter(status=2,owner=None).count()
        disable_configs_count = Service.objects.filter(status=1,owner=None).count()
        infinitconfs_count = Service.objects.filter(usage_limit=0,owner=None).count()
        infinit_time_confs_count = Service.objects.filter(expire_time=0,owner=None).count()

        buys_count_all_time = PurchaseRecord.objects.filter(created_for=None,type=0).count()
        tamdids_count_all_time = PurchaseRecord.objects.filter(created_for=None,type=1).count()
        perches_all_count_all_time = buys_count_all_time + tamdids_count_all_time
        buys_price_all_time = PurchaseRecord.objects.filter(created_for=None,type=0).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_all_time = PurchaseRecord.objects.filter(created_for=None,type=1).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_all_time = buys_price_all_time + tamdids_price_all_time
        deny_pays_count_all_time = BotPayment.objects.filter(status=9).count()

        buys_count_last_month = PurchaseRecord.objects.filter(created_for=None,type=0,date_time__range=(one_month_ago_time,now)).count()
        tamdids_count_last_month = PurchaseRecord.objects.filter(created_for=None,type=1,date_time__range=(one_month_ago_time,now)).count()
        perches_count_last_month = buys_count_last_month + tamdids_count_last_month
        buys_price_last_month = PurchaseRecord.objects.filter(created_for=None,type=0,date_time__range=(one_month_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_month = PurchaseRecord.objects.filter(created_for=None,type=1,date_time__range=(one_month_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_month = tamdids_price_last_month + buys_price_last_month

        buys_count_last_week = PurchaseRecord.objects.filter(created_for=None,type=0,date_time__range=(one_week_ago_time,now)).count()
        tamdids_count_last_week = PurchaseRecord.objects.filter(created_for=None,type=1,date_time__range=(one_week_ago_time,now)).count()
        perches_count_last_week = buys_count_last_week + tamdids_count_last_week
        buys_price_last_week = PurchaseRecord.objects.filter(created_for=None,type=0,date_time__range=(one_week_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_week = PurchaseRecord.objects.filter(created_for=None,type=1,date_time__range=(one_week_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_week = buys_price_last_week + tamdids_price_last_week

        buys_count_last_day = PurchaseRecord.objects.filter(created_for=None,type=0,date_time__range=(one_day_ago_time,now)).count()
        tamdids_count_last_day = PurchaseRecord.objects.filter(created_for=None,type=1,date_time__range=(one_day_ago_time,now)).count()
        perches_count_last_day = buys_count_last_day + tamdids_count_last_day
        buys_price_last_day = PurchaseRecord.objects.filter(created_for=None,type=0,date_time__range=(one_day_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_day = PurchaseRecord.objects.filter(created_for=None,type=1,date_time__range=(one_day_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_day = buys_price_last_day + tamdids_price_last_day

        data = { "configs_count": configs_count,"active_configs_count": active_configs_count,"ended_configs_count": ended_configs_count,
                 "disable_configs_count": disable_configs_count, "infinitconfs_count": infinitconfs_count,
                 "infinit_time_confs_count": infinit_time_confs_count, "perches_all_count_all_time": perches_all_count_all_time,
                 "buys_count_all_time": buys_count_all_time, "tamdids_count_all_time": tamdids_count_all_time,
                 "perches_price_all_time": perches_price_all_time, "buys_price_all_time": buys_price_all_time,
                 "tamdids_price_all_time": tamdids_price_all_time, "deny_pays_count_all_time": deny_pays_count_all_time,
                 "perches_count_last_month": perches_count_last_month,"buys_count_last_month": buys_count_last_month,
                 "tamdids_count_last_month": tamdids_count_last_month,"buys_price_last_month":buys_price_last_month,
                 "perches_price_last_month": perches_price_last_month, "tamdids_price_last_month":tamdids_price_last_month,
                 "buys_count_last_week":buys_count_last_week, "buys_count_last_day":buys_count_last_day,
                     "tamdids_count_last_week":tamdids_count_last_week, "tamdids_count_last_day":tamdids_count_last_day,
                 "perches_count_last_week":perches_count_last_week, "perches_count_last_day":perches_count_last_day,
                     "buys_price_last_week":buys_price_last_week, "buys_price_last_day":buys_price_last_day,
                 "tamdids_price_last_week":tamdids_price_last_week, "tamdids_price_last_day":tamdids_price_last_day,
                     "perches_price_last_week":perches_price_last_week, "perches_price_last_day":perches_price_last_day,
        }

        return render(request, "reportsbot.html", data)



class ReportsSellers(View, LoginRequiredMixin):
    def get(self, request):
        now = int(datetime.now().timestamp())
        one_month_ago_time = now - 2629800
        one_day_ago_time = now - 86400
        one_week_ago_time = now - 604800


        configs_count = Service.objects.filter(~Q(owner=None)).count()
        active_configs_count = Service.objects.filter(~Q(owner=None),status=0).count()
        ended_configs_count = Service.objects.filter(~Q(owner=None),status=2).count()
        disable_configs_count = Service.objects.filter(~Q(owner=None),status=1).count()
        infinitconfs_count = Service.objects.filter(~Q(owner=None),usage_limit=0).count()
        infinit_time_confs_count = Service.objects.filter(~Q(owner=None),expire_time=0).count()

        buys_count_all_time = PurchaseRecord.objects.filter(~Q(created_for=None),type=0).count()
        tamdids_count_all_time = PurchaseRecord.objects.filter(~Q(created_for=None),type=1).count()
        perches_all_count_all_time = buys_count_all_time + tamdids_count_all_time
        buys_price_all_time = PurchaseRecord.objects.filter(~Q(created_for=None),type=0).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_all_time = PurchaseRecord.objects.filter(~Q(created_for=None),type=1).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_all_time = buys_price_all_time + tamdids_price_all_time

        buys_count_last_month = PurchaseRecord.objects.filter(~Q(created_for=None),type=0,date_time__range=(one_month_ago_time,now)).count()
        tamdids_count_last_month = PurchaseRecord.objects.filter(~Q(created_for=None),type=1,date_time__range=(one_month_ago_time,now)).count()
        perches_count_last_month = buys_count_last_month + tamdids_count_last_month
        buys_price_last_month = PurchaseRecord.objects.filter(~Q(created_for=None),type=0,date_time__range=(one_month_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_month = PurchaseRecord.objects.filter(~Q(created_for=None),type=1,date_time__range=(one_month_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_month = tamdids_price_last_month + buys_price_last_month

        buys_count_last_week = PurchaseRecord.objects.filter(~Q(created_for=None),type=0,date_time__range=(one_week_ago_time,now)).count()
        tamdids_count_last_week = PurchaseRecord.objects.filter(~Q(created_for=None),type=1,date_time__range=(one_week_ago_time,now)).count()
        perches_count_last_week = buys_count_last_week + tamdids_count_last_week
        buys_price_last_week = PurchaseRecord.objects.filter(~Q(created_for=None),type=0,date_time__range=(one_week_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_week = PurchaseRecord.objects.filter(~Q(created_for=None),type=1,date_time__range=(one_week_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_week = buys_price_last_week + tamdids_price_last_week

        buys_count_last_day = PurchaseRecord.objects.filter(~Q(created_for=None),type=0,date_time__range=(one_day_ago_time,now)).count()
        tamdids_count_last_day = PurchaseRecord.objects.filter(~Q(created_for=None),type=1,date_time__range=(one_day_ago_time,now)).count()
        perches_count_last_day = buys_count_last_day + tamdids_count_last_day
        buys_price_last_day = PurchaseRecord.objects.filter(~Q(created_for=None),type=0,date_time__range=(one_day_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        tamdids_price_last_day = PurchaseRecord.objects.filter(~Q(created_for=None),type=1,date_time__range=(one_day_ago_time,now)).aggregate(Sum("price"))["price__sum"] or 0
        perches_price_last_day = buys_price_last_day + tamdids_price_last_day

        data = { "configs_count": configs_count,"active_configs_count": active_configs_count,"ended_configs_count": ended_configs_count,
                 "disable_configs_count": disable_configs_count, "infinitconfs_count": infinitconfs_count,
                 "infinit_time_confs_count": infinit_time_confs_count, "perches_all_count_all_time": perches_all_count_all_time,
                 "buys_count_all_time": buys_count_all_time, "tamdids_count_all_time": tamdids_count_all_time,
                 "perches_price_all_time": perches_price_all_time, "buys_price_all_time": buys_price_all_time,
                 "tamdids_price_all_time": tamdids_price_all_time,
                 "perches_count_last_month": perches_count_last_month,"buys_count_last_month": buys_count_last_month,
                 "tamdids_count_last_month": tamdids_count_last_month,"buys_price_last_month":buys_price_last_month,
                 "perches_price_last_month": perches_price_last_month, "tamdids_price_last_month":tamdids_price_last_month,
                 "buys_count_last_week":buys_count_last_week, "buys_count_last_day":buys_count_last_day,
                     "tamdids_count_last_week":tamdids_count_last_week, "tamdids_count_last_day":tamdids_count_last_day,
                 "perches_count_last_week":perches_count_last_week, "perches_count_last_day":perches_count_last_day,
                     "buys_price_last_week":buys_price_last_week, "buys_price_last_day":buys_price_last_day,
                 "tamdids_price_last_week":tamdids_price_last_week, "tamdids_price_last_day":tamdids_price_last_day,
                     "perches_price_last_week":perches_price_last_week, "perches_price_last_day":perches_price_last_day,
        }

        return render(request, "reports_sellers.html", data)

class ChartData(APIView):
    def get(self, request, r_type, format=None):
        now = int(datetime.now().timestamp())
        print(now)
        chartdata = []
        for week in range(0, 27):
            start = now - (week * 604800)
            end = now - ((week + 1) * 604800)
            print(start,end)
            if r_type == "all":
                buy = PurchaseRecord.objects.filter(type=0, date_time__range=(end, start)).count()
                tamdid = PurchaseRecord.objects.filter(type=1, date_time__range=(end, start)).count()
            elif r_type == "bot":
                buy = PurchaseRecord.objects.filter(created_for=None,type=0, date_time__range=(end, start)).count()
                tamdid = PurchaseRecord.objects.filter(created_for=None,type=1, date_time__range=(end, start)).count()
            else:
                buy = PurchaseRecord.objects.filter(~Q(created_for=None),type=0, date_time__range=(end, start)).count()
                tamdid = PurchaseRecord.objects.filter(~Q(created_for=None),type=1, date_time__range=(end, start)).count()
            print(buy, tamdid)
            chartdata.insert(0, buy+tamdid)
        labels = [
            "Now"
        ]
        for i in range(1,27):
            labels.insert(0, str(i))
        chartLabel = "بر اساس تعداد خرید و تمدید / هفته"

        data = {
            "labels": labels,
            "chartLabel": chartLabel,
            "chartdata": chartdata,
        }
        return Response(data)
