from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View

from bot.commands import CommandRunner
from sellers.models import SubSellerSubset
from accounts.models import User
from .forms import CreateConfigForm, ManualCreateConfigForm, SearchConfigForm, SellersCreateConfigForm, ManualSellersCreateConfigForm
from finance.models import Prices, SellersPrices
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from time import sleep
from .models import ConfigJobsQueue, Service, Config
import uuid
import json
from servers.models import Server
from persiantools.jdatetime import JalaliDateTime
from os import environ
from django.http import HttpResponse
from random import shuffle
from datetime import datetime
import urllib.parse
from configs.tasks import run_jobs


class ConfigAction:
    @staticmethod
    def generate_config_name():
        with open("settings.json", "r+") as f:
            setting = json.load(f)
            counter = setting["config_name_counter"]
            setting["config_name_counter"] += 1
            f.seek(0)
            json.dump(setting, f)
            f.truncate()
            return str(counter)



    @staticmethod
    def create_config_db(service_uuid):
        service = Service.objects.get(uuid=service_uuid)
        for server in Server.objects.all():
            Config.objects.create(
                status=-1,
                server=server,
                service=service,
                last_update=int(JalaliDateTime.now().timestamp())
            ).save()


    @staticmethod
    def create_config_job_queue(service_uuid, job):
        service = Service.objects.get(uuid=service_uuid)
        for config in Config.objects.filter(service=service):
            ConfigJobsQueue.objects.create(
                config=config,
                job=job,
            ).save()

    @staticmethod
    def reset_config_db(service_uuid):
        configs = Config.objects.filter(service__uuid=service_uuid)
        for config in configs:
            config.usage = 0
            config.save()



class BotCreateConfigView(LoginRequiredMixin, View):
    def get(self, request, form_type):
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        return render(request, 'create_config.html',
                      {'form': forms[form_type], 'form_type': form_type})

    def post(self, request, form_type):
        from finance.views import FinanceAction
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        form = forms[form_type](request.POST)
        if form.is_valid():
            ip_limit = 0
            time_limit = 0
            usage = 0
            cd = form.cleaned_data

            if cd['type'] == "limited":
                usage = int(cd["usage_limit"])
                time_limit = int(cd['days_limit'])
            elif cd['type'] == 'usage_unlimit':
                time_limit = int(cd['days_limit'])
                ip_limit = int(cd['ip_limit'])
            elif cd['type'] == 'time_unlimit':
                usage = int(cd["usage_limit"])

            if form_type == 'auto':
                price = Prices.objects.get(usage_limit=usage, expire_limit=time_limit, user_limit=ip_limit).price
            else:
                price = cd['price']
            paid = cd["paid"]
            if form_type == 'auto':
                time_limit = time_limit * 30
            service_uuid = uuid.uuid4()
            service_name = ConfigAction.generate_config_name()
            Service.objects.create(
                uuid=service_uuid,
                name=service_name,
                usage_limit=usage,
                expire_time=time_limit,
                user_limit=ip_limit,
                paid=paid,
                created_by=request.user,
            ).save()
            ConfigAction.create_config_db(service_uuid)
            ConfigAction.create_config_job_queue(service_uuid, 0)
            run_jobs.delay()
            FinanceAction.create_purchase_record(None, request.user, price, 0, f"{usage}GB / {time_limit}d / {ip_limit}u", service_name)
            return redirect('configs:conf_page', str(service_uuid))
        return render(request, 'create_config.html', {'form': form, 'form_type': form_type})

class BotRenewConfigView(LoginRequiredMixin, View):
    def get(self, request, config_uuid, form_type):
        service = Service.objects.get(uuid=config_uuid)
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        return render(request, 'renew_config.html',
                      {'form': forms[form_type], 'form_type': form_type, "service": service})

    def post(self, request, config_uuid, form_type):
        from finance.views import FinanceAction
        service = Service.objects.get(uuid=config_uuid)
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        form = forms[form_type](request.POST)
        if form.is_valid():
            ip_limit = 0
            time_limit = 0
            usage = 0
            cd = form.cleaned_data

            if cd['type'] == "limited":
                usage = int(cd["usage_limit"])
                time_limit = int(cd['days_limit'])
            elif cd['type'] == 'usage_unlimit':
                time_limit = int(cd['days_limit'])
                ip_limit = int(cd['ip_limit'])
            elif cd['type'] == 'time_unlimit':
                usage = int(cd["usage_limit"])

            if form_type == 'auto':
                price = Prices.objects.get(usage_limit=usage, expire_limit=time_limit, user_limit=ip_limit).price
            else:
                price = cd['price']
            paid = cd["paid"]
            if form_type == 'auto':
                time_limit = time_limit * 30

            service.usage_limit = usage
            service.expire_time = (datetime.now().timestamp() + (time_limit * 86400)) if service.start_time != 0 else time_limit
            service.user_limit = ip_limit
            service.paid = paid
            service.save()
            ConfigAction.create_config_job_queue(service.uuid, 4)
            ConfigAction.reset_config_db(service.uuid)
            run_jobs.delay()
            if service.customer:
                CommandRunner.send_msg(service.customer.chat_id, f"سرویس {service.name} تمدید شد.")
            FinanceAction.create_purchase_record(None, request.user, price, 1, f"{usage}GB / {time_limit}d / {ip_limit}u", service.name)
            messages.success(request, f'سروریس {service.name} در صف تمدید قرار گرفت. این فرایند ممکن است چندین دقیقه طول بکشد.')

            return redirect('configs:conf_page', str(service.uuid))
        return render(request, 'renew_config.html', {'form': form, 'form_type': form_type, "service": service})




class BotListConfigView(LoginRequiredMixin, View):
    def get(self, request,*args, **kwargs):
        data = Service.objects.filter(owner=None)
        searchform = SearchConfigForm()
        return render(request, "list_configs.html", {"data": data, 'searchform': searchform})

    def post(self, request, *args, **kwargs):
        searchform = SearchConfigForm(request.POST)
        if searchform.is_valid():
            word = searchform.cleaned_data["search_config"]
            data = Service.objects.filter(Q(name__icontains=word) | Q(uuid__icontains=word),owner=None)
            return render(request, "list_configs.html",
                          {"data": data, "searchform": searchform, "searched": True})

class ConfigPage(LoginRequiredMixin, View):
    def get(self, request, config_uuid):
        if Service.objects.filter(uuid=config_uuid).exists():
            service = Service.objects.get(uuid=config_uuid)
            sub_link_domain = environ.get("SUB_LINK_DOMAIN")
            sub_link_domain = "https://" + sub_link_domain.replace("https://", "").replace("http://", "")
            sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{config_uuid}/")
            sub_link = ('کانفیگ شما: \n\n  ' + sub_link + "")
        else:
            service = False
        get_config_link = f"نام سرویس: {service.name}" "\n\n" "برای دریافت کانفیگ روی لینک زیر کلیک کنید 👇🏻" "\n"  f'tg://resolve?domain={environ.get('BOT_USERNAME')}&start=register_{config_uuid}'
        return render(request, 'config_page.html', {'service': service, 'sub_link': sub_link, "get_config_link":get_config_link})

class DeleteConfig(LoginRequiredMixin, View):
    def get(self, request, config_uuid):
        service = Service.objects.get(uuid=config_uuid)
        service.status = 4
        service.save()
        for config in Config.objects.filter(service=service):
            ConfigJobsQueue.objects.create(
                config=config,
                job=2,
            ).save()
        run_jobs.delay()
        messages.success(request, f"سرویس {service.name} در صف حذف قرار گرفت.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

class DisableConfig(LoginRequiredMixin, View):
    def get(self, request, config_uuid, enable):
        service = Service.objects.get(uuid=config_uuid)
        service.status = 0 if enable else 1
        service.save()
        for config in Config.objects.filter(service=service):
            ConfigJobsQueue.objects.create(
                config=config,
                job=3 if enable else 1,
            ).save()
            config.status = 2
            config.save()

            run_jobs.delay()

        return redirect(request.META.get('HTTP_REFERER', '/'))


class ClientsConfigPage(View):
    def get(self, request, config_uuid):
        if Service.objects.filter(uuid=config_uuid).exists():
            service = Service.objects.get(uuid=config_uuid)
            sub_link_domain = environ.get("SUB_LINK_DOMAIN")
            sub_link_domain = "https://" + sub_link_domain.replace("https://", "").replace("http://", "")
            sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{config_uuid}/")
        else:
            service = False
            sub_link = False
        return render(request, 'client_config_page.html', {'service': service, 'sub_link': sub_link})


class Sublink(APIView):
    def get(self, request, config_uuid):
        if Service.objects.filter(uuid=config_uuid).exists():
            service = Service.objects.get(uuid=config_uuid)
            content = []
            for server in Server.objects.all():
                content.append(f"vless://{config_uuid}@{server.fake_domain}:{server.inbound_port}?type=tcp&path=%2F&host=speedtest.net&headerType=http&security=none#Napsv_{service.name} / {server.name}")
            shuffle(content)
            content_str = ""
            for i in content:
                content_str += (i + "\n")
            user_agent = request.headers.get('User-Agent', None)
            is_v2ray_client = any(word in user_agent for word in ["hiddify", "v2ray"])
            if is_v2ray_client:
                service_obj = Service.objects.get(uuid=config_uuid)
                if not service_obj.expire_time == 0 and service_obj.start_time == 0:
                    time_stamp = datetime.now().timestamp()
                    service_obj.start_time = time_stamp
                    service_obj.expire_time = time_stamp + (service_obj.expire_time * 86400)
                    service_obj.save()
                response = HttpResponse(content_str)
                response['Content-Disposition'] = f'attachment; filename="Napsv_{service.name}"'
                return response
            else:
                return redirect("configs:client_config_page",config_uuid)
        else:
            return HttpResponse(status=404)

    def post(self, request, config_uuid):
        return HttpResponse(status=404)

# Api


class ApiGetConfigTimeChoices(APIView):
    def get(self, request):
        sleep(0.25)
        type = request.GET.get('type')
        choices = []
        if type == 'limited':
            obj = Prices.objects.filter(~Q(usage_limit=0) & ~Q(expire_limit=0))
            for i in obj:
                if not (i.expire_limit, f"{i.expire_limit} ماه") in choices:
                    choices.append((i.expire_limit, f"{i.expire_limit} ماه"))
        elif type == 'usage_unlimit':
            obj = Prices.objects.filter(Q(usage_limit=0) & ~Q(expire_limit=0))
            for i in obj:
                if not (i.expire_limit, f"{i.expire_limit} ماه") in choices:
                    choices.append((i.expire_limit, f"{i.expire_limit} ماه"))
        elif type == 'time_unlimit':
            choices.append((0, '∞'))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiGetConfigUsageChoices(APIView):
    def get(self, request):
        type = request.GET.get('type')
        time = int(request.GET.get('time'))
        choices = []
        if type == 'limited':
            time = time
            obj = Prices.objects.filter(~Q(usage_limit=0) & Q(expire_limit=time))
            for i in obj:
                if not (i.usage_limit, f"{i.usage_limit} GB") in choices:
                    choices.append((i.usage_limit, f"{i.usage_limit} GB"))

        elif type == 'usage_unlimit':
            choices.append((0, '∞'))

        elif type == 'time_unlimit':
            obj = Prices.objects.filter(~Q(usage_limit=0) & Q(expire_limit=0))
            for i in obj:
                if not (i.usage_limit, f"{i.usage_limit} GB") in choices:
                    choices.append((i.usage_limit, f"{i.usage_limit} GB"))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiGetConfigIPLimitChoices(APIView):
    def get(self, request):
        type = request.GET.get('type')
        time = int(request.GET.get('time'))

        choices = []
        if type == 'limited' or type == 'time_unlimit':
            choices.append((0, '∞'))

        elif type == 'usage_unlimit':
            time = time
            obj = Prices.objects.filter(Q(usage_limit=0) & Q(expire_limit=time))
            for i in obj:
                if not (i.user_limit, f"{i.user_limit} کاربره") in choices:
                    choices.append((i.user_limit, f"{i.user_limit} کاربره"))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiGetConfigPriceChoices(APIView):
    def get(self, request):
        time = int(request.GET.get('time'))
        iplimit = int(request.GET.get('iplimit'))
        usage = int(request.GET.get('usage'))
        obj = Prices.objects.get(usage_limit=usage, expire_limit=time, user_limit=iplimit).price
        return Response({'price': f'{obj:,}'})



#####################################################################


#####################       Sellers View      #######################


#####################################################################





class SellersCreateConfigView(LoginRequiredMixin, View):
    def get(self, request, username, form_type):
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        return render(request, 'sellers_create_config.html',
                      {'form': forms[form_type], 'form_type': form_type, "seller_username": username})

    def post(self, request, username, form_type):
        from finance.views import FinanceAction
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        owner = User.objects.get(username=username)
        form = forms[form_type](request.POST)
        if form.is_valid():
            ip_limit = 0
            time_limit = 0
            usage = 0
            cd = form.cleaned_data

            if cd['type'] == "limited":
                usage = int(cd["usage_limit"])
                time_limit = int(cd['days_limit'])
            elif cd['type'] == 'usage_unlimit':
                time_limit = int(cd['days_limit'])
                ip_limit = int(cd['ip_limit'])
            elif cd['type'] == 'time_unlimit':
                usage = int(cd["usage_limit"])

            if form_type == 'auto':
                price = SellersPrices.objects.get(seller=owner,usage_limit=usage, expire_limit=time_limit, user_limit=ip_limit).price
            else:
                price = cd['price']
            price *= 1000
            if form_type == 'auto':
                time_limit = time_limit * 30
            service_uuid = uuid.uuid4()
            service_name = ConfigAction.generate_config_name()
            Service.objects.create(
                uuid=service_uuid,
                name=service_name,
                usage_limit=usage,
                expire_time=time_limit,
                user_limit=ip_limit,
                created_by=request.user,
                owner=owner,
            ).save()
            ConfigAction.create_config_db(service_uuid)
            ConfigAction.create_config_job_queue(service_uuid, 0)
            run_jobs.delay()
            FinanceAction.create_purchase_record(owner, request.user, price, 0, f"{usage}GB / {time_limit}d / {ip_limit}u", service_name)
            return redirect('configs:sellers_conf_page', str(service_uuid))
        return render(request, 'sellers_create_config.html', {'form': form, 'form_type': form_type})



class SellersRenewConfigView(LoginRequiredMixin, View):
    def get(self, request, config_uuid, username, form_type):
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        service = Service.objects.get(uuid=config_uuid)
        return render(request, 'sellers_create_config.html',
                      {'form': forms[form_type], 'form_type': form_type, "seller_username": username})

    def post(self, request, config_uuid, username, form_type):
        from finance.views import FinanceAction
        forms = {'auto': CreateConfigForm, 'manual': ManualCreateConfigForm}
        service = Service.objects.get(uuid=config_uuid)
        owner = User.objects.get(username=username)
        form = forms[form_type](request.POST)
        if form.is_valid():
            ip_limit = 0
            time_limit = 0
            usage = 0
            cd = form.cleaned_data
            if cd['type'] == "limited":
                usage = int(cd["usage_limit"])
                time_limit = int(cd['days_limit'])
            elif cd['type'] == 'usage_unlimit':
                time_limit = int(cd['days_limit'])
                ip_limit = int(cd['ip_limit'])
            elif cd['type'] == 'time_unlimit':
                usage = int(cd["usage_limit"])

            if form_type == 'auto':
                price = SellersPrices.objects.get(seller=owner,usage_limit=usage, expire_limit=time_limit, user_limit=ip_limit).price
            else:
                price = cd['price']
            price *= 1000
            if form_type == 'auto':
                time_limit = time_limit * 30

            service.usage_limit = usage
            service.expire_time = (datetime.now().timestamp() + (time_limit * 86400)) if service.start_time != 0 else time_limit
            service.user_limit = ip_limit
            service.save()
            ConfigAction.create_config_job_queue(service.uuid, 4)
            ConfigAction.reset_config_db(service.uuid)
            run_jobs.delay()

            FinanceAction.create_purchase_record(owner, request.user, price, 1, f"{usage}GB / {time_limit}d / {ip_limit}u", service.name)
            messages.success(request, f'سروریس {service.name} در صف تمدید قرار گرفت. این فرایند ممکن است چندین دقیقه طول بکشد.')
            return redirect('configs:sellers_conf_page', str(service.uuid))
        return render(request, 'sellers_create_config.html', {'form': form, 'form_type': form_type})



class SellersListConfigView(LoginRequiredMixin, View):
    def get(self, request,username,*args, **kwargs):
        if request.user.level_access == 10:
            if username == "all":
                data = Service.objects.filter(~Q(owner=None))
            else:
                data = Service.objects.filter(owner__username=username)
        elif request.user.level_access == 1:
            if username == "all":
                sub_list = [seller.sub for seller in SubSellerSubset.objects.filter(head=request.user)]
                sub_list.append(request.user)
                data = Service.objects.filter(Q(owner__in=sub_list))
            else:
                data = Service.objects.filter(owner__username=username)
        else:
            data = Service.objects.filter(owner=request.user)

        searchform = SearchConfigForm()
        return render(request, "sellers_list_configs.html", {"data": data, 'searchform': searchform, "username":username})

    def post(self, request, username ,*args, **kwargs):
        searchform = SearchConfigForm(request.POST)
        if searchform.is_valid():
            word = searchform.cleaned_data["search_config"]

            if request.user.level_access == 10:
                if username == "all":
                    data = Service.objects.filter(Q(name__icontains=word) | Q(uuid__icontains=word),~Q(owner=None))
                else:
                    data = Service.objects.filter(Q(name__icontains=word) | Q(uuid__icontains=word),owner__username=username)
            elif request.user.level_access == 1:
                if username == "all":
                    sub_list = [seller.sub for seller in SubSellerSubset.objects.filter(head=request.user)]
                    sub_list.append(request.user)
                    data = Service.objects.filter(Q(name__icontains=word) | Q(uuid__icontains=word),Q(owner__in=sub_list))
                else:
                    data = Service.objects.filter(Q(name__icontains=word) | Q(uuid__icontains=word),owner__username=username)
            else:
                data = Service.objects.filter(Q(name__icontains=word) | Q(uuid__icontains=word),owner=request.user)

            return render(request, "sellers_list_configs.html",
                          {"data": data, "searchform": searchform, "searched": True, "username":username})


class SellersConfigPage(LoginRequiredMixin, View):
    def get(self, request, config_uuid):
        if Service.objects.filter(uuid=config_uuid).exists():
            service = Service.objects.get(uuid=config_uuid)
            get_config_link = f"نام سرویس: {service.name}" "\n\n" "برای دریافت کانفیگ روی لینک زیر کلیک کنید 👇🏻" "\n"  f'tg://resolve?domain={environ.get('BOT_USERNAME')}&start=register_{config_uuid}'
            sub_link_domain = environ.get("SUB_LINK_DOMAIN")
            sub_link_domain = "https://" + sub_link_domain.replace("https://","").replace("http://","")
            sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{config_uuid}/")
            sub_link = ('کانفیگ شما: \n\n  ' + sub_link + "")
        else:
            service = False
            sub_link = False

        return render(request, 'sellers_config_page.html', {'service': service, 'sub_link': sub_link})

####### sellers api


class ApiSellersGetConfigTimeChoices(APIView):
    def get(self, request):
        sleep(0.25)
        seller_username = request.GET.get('username')
        print(seller_username)
        type = request.GET.get('type')
        choices = []
        if type == 'limited':
            obj = SellersPrices.objects.filter(~Q(usage_limit=0) & ~Q(expire_limit=0),seller__username=seller_username)
            for i in obj:
                if not (i.expire_limit, f"{i.expire_limit} ماه") in choices:
                    choices.append((i.expire_limit, f"{i.expire_limit} ماه"))
        elif type == 'usage_unlimit':
            obj = SellersPrices.objects.filter(Q(usage_limit=0) & ~Q(expire_limit=0),seller__username=seller_username)
            for i in obj:
                if not (i.expire_limit, f"{i.expire_limit} ماه") in choices:
                    choices.append((i.expire_limit, f"{i.expire_limit} ماه"))
        elif type == 'time_unlimit':
            choices.append((0, '∞'))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiSellersGetConfigUsageChoices(APIView):
    def get(self, request):
        seller_username = request.GET.get('username')
        type = request.GET.get('type')
        time = int(request.GET.get('time'))
        choices = []
        if type == 'limited':
            time = time
            obj = SellersPrices.objects.filter(~Q(usage_limit=0) & Q(expire_limit=time),seller__username=seller_username)
            for i in obj:
                if not (i.usage_limit, f"{i.usage_limit} GB") in choices:
                    choices.append((i.usage_limit, f"{i.usage_limit} GB"))

        elif type == 'usage_unlimit':
            choices.append((0, '∞'))

        elif type == 'time_unlimit':
            obj = SellersPrices.objects.filter(~Q(usage_limit=0) & Q(expire_limit=0),seller__username=seller_username)
            for i in obj:
                if not (i.usage_limit, f"{i.usage_limit} GB") in choices:
                    choices.append((i.usage_limit, f"{i.usage_limit} GB"))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiSellersGetConfigIPLimitChoices(APIView):
    def get(self, request):
        seller_username = request.GET.get('username')
        type = request.GET.get('type')
        time = int(request.GET.get('time'))

        choices = []
        if type == 'limited' or type == 'time_unlimit':
            choices.append((0, '∞'))

        elif type == 'usage_unlimit':
            time = time
            obj = SellersPrices.objects.filter(Q(usage_limit=0) & Q(expire_limit=time),seller__username=seller_username)
            for i in obj:
                if not (i.user_limit, f"{i.user_limit} کاربره") in choices:
                    choices.append((i.user_limit, f"{i.user_limit} کاربره"))

        choices = sorted(choices, key=lambda x: x[0])
        return Response({'choices': choices})


class ApiSellersGetConfigPriceChoices(APIView):
    def get(self, request):
        seller_username = request.GET.get('username')
        time = int(request.GET.get('time'))
        iplimit = int(request.GET.get('iplimit'))
        usage = int(request.GET.get('usage'))
        obj = SellersPrices.objects.get(usage_limit=usage, expire_limit=time, user_limit=iplimit,seller__username=seller_username   ).price
        return Response({'price': f'{obj:,}'})