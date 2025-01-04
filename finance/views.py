from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Sum
from accounts.models import User
from sellers.models import SubSellerSubset
from .forms import EditPayPriceForm, AddPriceForm, AddOffForm, SellersAddPriceForm, PriceForm
from customers.models import Customer
from .models import BotPayment, OffCodes, SellersPrices,Prices, PurchaseRecord
from bot.commands import CommandRunner
from persiantools.jdatetime import JalaliDateTime
import os
from configs.views import ConfigAction
from configs.models import Service
import uuid
from configs.tasks import run_jobs
from datetime import datetime

class FinanceAction:
    @staticmethod
    def change_wallet(amount, chat_id):
        print(amount)
        customer = Customer.objects.get(chat_id=chat_id)
        customer.wallet = amount + customer.wallet
        customer.save()

    @staticmethod
    def create_purchase_record(created_for, created_by, price, type_pay, description, service_name):
        PurchaseRecord.objects.create(
            created_for=created_for,
            created_by=created_by,
            price=price,
            type=type_pay,
            description=description,
            date_time=datetime.now().timestamp(),
            service_name=service_name,
        ).save()


class ConfirmPaymentPage(LoginRequiredMixin, View):
    def get(self, request, show_box):
        pay_queue_obj = BotPayment.objects.filter(status=0)
        second_pay_queue_obj = BotPayment.objects.filter(status=1)
        not_paid_obj = Service.objects.filter(paid=False, owner=None)
        if not pay_queue_obj.exists() and not second_pay_queue_obj.exists():
            messages.info(request, "پرداختی برای تایید نمانده است. \n برای اطمینان یکبار صفحه را رفرش کنید.")
        return render(request, 'confirm_payment.html',
                      {'confirm': pay_queue_obj, "confirm_count": pay_queue_obj.count(),
                       "second_confirm": second_pay_queue_obj, "second_confirm_count": second_pay_queue_obj.count(),
                       "not_paid": not_paid_obj, "not_paid_count": not_paid_obj.count(),
                       "show_box": show_box})


class FirstConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        pay_obj = BotPayment.objects.get(id=obj_id)
        FinanceAction.change_wallet(pay_obj.price, pay_obj.customer.chat_id)
        if pay_obj.status == 0:
            if pay_obj.action == 0: # add to wallet
                CommandRunner.send_msg(pay_obj.customer.chat_id, f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد.")
            elif pay_obj.action == 1: # buy service
                CommandRunner.send_msg(pay_obj.customer.chat_id, "پرداخت شما تایید شد. لینک سرویس برای شما ارسال میشود.")
                if Customer.objects.get(chat_id=pay_obj.customer.chat_id).wallet >= pay_obj.info["config_price"]:

                    service_uuid = uuid.uuid4()
                    service_name = ConfigAction.generate_config_name()
                    Service.objects.create(
                        uuid=service_uuid,
                        name=service_name,
                        usage_limit=pay_obj.info["usage_limit"],
                        expire_time=pay_obj.info["expire_time"] * 30,
                        user_limit=pay_obj.info["user_limit"],
                        customer=pay_obj.customer,
                    ).save()
                    pay_obj.service_uuid = service_uuid
                    ConfigAction.create_config_db(service_uuid)
                    ConfigAction.create_config_job_queue(service_uuid, 0)
                    FinanceAction.change_wallet(pay_obj.info["config_price"] * -1, pay_obj.customer.chat_id)
                    CommandRunner.send_msg(pay_obj.customer.chat_id,f"پرداخت شما تایید شد و لینک سرویس برای شما ارسال میشود.")
                    CommandRunner.send_sub_link(service_uuid)
                    run_jobs.delay()
                    FinanceAction.create_purchase_record(None, None, pay_obj.info["config_price"], 0,f"{pay_obj.info["usage_limit"]}GB / {pay_obj.info["expire_time"] * 30}d / {pay_obj.info["user_limit"]}u", service_name)
                else:
                    CommandRunner.send_msg(pay_obj.customer.chat_id,
                                           f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد. اما این مبلغ برای خرید کانفیگ انتخابی کافی نیست.")
            elif pay_obj.action == 2: # renew service
                if Customer.objects.get(chat_id=pay_obj.customer.chat_id).wallet >= pay_obj.info["config_price"]:
                    service = Service.objects.get(uuid=pay_obj.info["service_uuid"])
                    service.usage_limit = pay_obj.info["usage_limit"]
                    if pay_obj.info["expire_time"] == 0:
                        service.expire_time = 0
                    else:
                        service.expire_time = (datetime.now().timestamp() + (pay_obj.info["expire_time"] * 86400)) if service.start_time != 0 else pay_obj.info["expire_time"]
                    service.user_limit = pay_obj.info["user_limit"]
                    service.save()
                    pay_obj.service_uuid = service.uuid
                    ConfigAction.create_config_job_queue(service.uuid, 4)
                    FinanceAction.change_wallet(pay_obj.info["config_price"] * -1, pay_obj.customer.chat_id)
                    ConfigAction.reset_config_db(service.uuid)
                    run_jobs.delay()
                    CommandRunner.send_msg(service.customer.chat_id, f"پرداخت شما تایید و سرویس {service.name} تمدید شد. ✅ ")
                    FinanceAction.create_purchase_record(None, None, pay_obj.info["config_price"], 1,
                                                         f"{pay_obj.info["usage_limit"]}GB / {pay_obj.info["expire_time"] * 30}d / {pay_obj.info["user_limit"]}u",service.name)
                else:
                    CommandRunner.send_msg(pay_obj.customer.chat_id,
                                           f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد. اما این مبلغ برای تمدید سرویس مورد نظر کافی نیست.")

            pay_obj.status = 1
            pay_obj.save()
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 1)


class SecondConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        pay_obj = BotPayment.objects.get(id=obj_id)
        FinanceAction.change_wallet(pay_obj.price, pay_obj.customer.chat_id)
        if pay_obj.status == 0:
            if pay_obj.action == 0:  # add to wallet
                CommandRunner.send_msg(pay_obj.customer.chat_id,
                                       f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد.")
            elif pay_obj.action == 1:  # buy service
                if Customer.objects.get(chat_id=pay_obj.customer.chat_id).wallet >= pay_obj.info["config_price"]:
                    service_uuid = uuid.uuid4()
                    service_name = ConfigAction.generate_config_name()
                    Service.objects.create(
                        uuid=service_uuid,
                        name=service_name,
                        usage_limit=pay_obj.info["usage_limit"],
                        expire_time=pay_obj.info["expire_time"] * 30,
                        user_limit=pay_obj.info["user_limit"],
                        customer=pay_obj.customer,
                    ).save()
                    pay_obj.service_uuid = service_uuid
                    ConfigAction.create_config_db(service_uuid)
                    ConfigAction.create_config_job_queue(service_uuid, 0)
                    FinanceAction.change_wallet(pay_obj.info["config_price"] * -1, pay_obj.customer.chat_id)
                    CommandRunner.send_msg(pay_obj.customer.chat_id,f"پرداخت شما تایید شد و لینک سرویس برای شما ارسال میشود.")
                    CommandRunner.send_sub_link(service_uuid)
                    run_jobs.delay()

                    FinanceAction.create_purchase_record(None, None, pay_obj.info["config_price"], 0,f"{pay_obj.info["usage_limit"]}GB / {pay_obj.info["expire_time"] * 30}d / {pay_obj.info["user_limit"]}u", service_name)
                else:
                    CommandRunner.send_msg(pay_obj.customer.chat_id,
                                           f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد. اما این مبلغ برای خرید کانفیگ انتخابی کافی نیست.")
            elif pay_obj.action == 2:  # renew service
                if Customer.objects.get(chat_id=pay_obj.customer.chat_id).wallet >= pay_obj.info["config_price"]:
                    service = Service.objects.get(uuid=pay_obj.info["service_uuid"])
                    service.usage_limit = pay_obj.info["usage_limit"]
                    if pay_obj.info["expire_time"] == 0:
                        service.expire_time = 0
                    else:
                        service.expire_time = (datetime.now().timestamp() + (pay_obj.info["expire_time"] * 86400)) if service.start_time != 0 else pay_obj.info["expire_time"]
                    service.save()
                    pay_obj.service_uuid = service.uuid
                    ConfigAction.create_config_job_queue(service.uuid, 4)
                    FinanceAction.change_wallet(pay_obj.info["config_price"] * -1, pay_obj.customer.chat_id)
                    ConfigAction.reset_config_db(service.uuid)
                    run_jobs.delay()
                    CommandRunner.send_msg(service.customer.chat_id, f"پرداخت شما تایید و سرویس {service.name} تمدید شد. ✅ ")
                    FinanceAction.create_purchase_record(None, None, pay_obj.info["config_price"], 1,
                                                         f"{pay_obj.info["usage_limit"]}GB / {pay_obj.info["expire_time"] * 30}d / {pay_obj.info["user_limit"]}u",service.name)
                else:
                    CommandRunner.send_msg(pay_obj.customer.chat_id,
                                           f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد. اما این مبلغ برای تمدید سرویس مورد نظر کافی نیست.")


            pay_obj.status = 2
            pay_obj.save()
            messages.success(request, "پرداخت با موفقیت تایید شد.")
        elif pay_obj.status == 1:
            pay_obj.status = 2
            pay_obj.save()
            messages.success(request, "پرداخت با موفقیت تایید شد.")

        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 1)


class DenyPaymentPage(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        deny_reason = ""
        pay_obj = BotPayment.objects.get(id=obj_id)
        CommandRunner.send_msg(pay_obj.customer.chat_id, f"پرداخت شما تایید نشد ❌ ")
        if pay_obj.status == 1:
            if pay_obj.action == 0:
                pay_obj = BotPayment.objects.get(id=obj_id)
                FinanceAction.change_wallet(pay_obj.price * -1, pay_obj.customer.chat_id)
            else:
                service = Service.objects.get(uuid=pay_obj.service_uuid)
                service.status = 4
                service.save()
                ConfigAction.create_config_job_queue(service.uuid, 2, request.user)
                run_jobs.delay()
                messages.success(request, f"سرویس {service.name} در صف حذف قرار گرفت.")
                CommandRunner.send_msg(pay_obj.customer.chat_id, f"سرویس {service.name} حذف شد ❌")


        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        pay_obj.status = 9
        pay_obj.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))

    def post(self, request, obj_id):
        pass

class EditPricePayment(LoginRequiredMixin, View):
    def get(self, request, obj_id, typ):
        form = EditPayPriceForm
        model_obj = BotPayment.objects.get(id=obj_id)
        return render(request, 'edit_price_payment.html', {'obj': model_obj, 'form': form})

    def post(self, request, obj_id, typ):
        form = EditPayPriceForm(request.POST)
        model_obj = BotPayment.objects.get(id=obj_id)
        if form.is_valid():
            price = form.cleaned_data['price']
            model_obj.price = price
            model_obj.save()
            messages.success(request, "مبلغ با موفقیت تغییر کرد. از لیست زیر آن را تایید کنید.")
            return redirect('finance:confirm_payments', 1)
        return render(request, 'edit_price_payment.html', {'obj': model_obj, 'form': form})



class ShowPrices(LoginRequiredMixin, View):
    def get(self, request):
        price_model = Prices.objects.all().order_by('expire_limit', 'usage_limit')
        return render(request, 'show_prices.html', {'price_model': price_model})


class DeleteOrEditPrice(LoginRequiredMixin, View):
    def get(self, request, obj_id, action):
        model_obj = Prices.objects.get(id=obj_id)
        if action == "delete":
            model_obj.delete()
            messages.success(request, "تعرفه با موفقیت حذف شد.")
            return redirect('finance:show_prices')


class AddPrice(LoginRequiredMixin, View):
    def get(self, request):
        form = AddPriceForm()
        return render(request, 'AddPrice.html', {'form': form})

    def post(self, request):
        form = AddPriceForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if cd["type_conf"] == "limited":
                usage = cd["usage"]
                month = cd["month"]
                ip_limit = 0
            elif cd["type_conf"] == "inf_usage":
                usage = 0
                month = cd['month']
                ip_limit = cd["ip_limit"]
            elif cd["type_conf"] == "inf_time":
                usage = cd["usage"]
                month = 0
                ip_limit = 0
            price = cd["price"] * 1000

            Prices.objects.create(
                price=price,
                expire_limit=int(month),
                user_limit=int(ip_limit),
                usage_limit=int(usage),
            ).save()
            return redirect('finance:show_prices')
        return render(request, 'AddPrice.html', {'form': form})


class AddOffCode(LoginRequiredMixin, View):
    def get(self, request):
        form = AddOffForm
        return render(request, "add_off_code.html", {"form": form})

    def post(self, request):
        form = AddOffForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            OffCodes.objects.create(
                type_off=bool(int(cd["type_off"])),
                amount=cd["amount"],
                customer_count=cd["curumer_count"],
                use_count=cd["use_count"],
                create_timestamp=int(JalaliDateTime.now().timestamp()),
                end_timestamp=int(JalaliDateTime.now().timestamp()) + (int(cd["end_time"]) * 86400),
                for_infinit_usages=cd["for_infinit_usages"],
                for_infinit_times=cd["for_infinit_times"],
                for_not_infinity=cd["for_not_infinity"],
            )
            return redirect("finance:show_off_codes")
        return render(request, "add_off_code.html", {"form": form})


class ShowOffCodes(LoginRequiredMixin, View):
    def get(self, request):
        model_obj = OffCodes.objects.all().order_by('-id')
        BOT_USERNAME = os.environ.get('BOT_USERNAME')
        return render(request, "show_off_codes.html", {"model_obj":model_obj, "bot_username":BOT_USERNAME})


class DeleteOffCode(LoginRequiredMixin, View):
    def get(self, request, uuid):
        OffCodes.objects.get(uid=uuid).delete()
        return redirect("finance:show_off_codes")


class SellersSumBills(LoginRequiredMixin, View):
    def get(self, request):
        sub_list = {sub.sub: sub.head for sub in SubSellerSubset.objects.all()}
        sellers_list = {}
        for seller in User.objects.filter(level_access__in=[0,1]):
            sum_prices = sum(p.price if p.type in [0,1] else p.price * -1 for p in PurchaseRecord.objects.filter(created_for=seller))
            if seller in sub_list.keys():
                seller = sub_list[seller]
            if seller in sellers_list.keys():
                sellers_list[seller] += sum_prices
            else:
                sellers_list[seller] = sum_prices
        sum_bills = sum(sellers_list.values())
        return render(request, 'sellers_sum_bills.html', {"sellers": sellers_list, "sum_bills": sum_bills})


class SellerPayBills(LoginRequiredMixin, View):
    def get(self, request, username):
        list_of_subs = [sub.sub for sub in SubSellerSubset.objects.filter(head__username=username)]
        list_of_subs.append(User.objects.get(username=username))
        purchases = PurchaseRecord.objects.filter(created_for__in=list_of_subs).order_by("date_time")
        sum_bills = sum(p.price if p.type in [0,1] else p.price * -1 for p in purchases)
        form = PriceForm
        return render(request, 'seller_pay_page.html',
                      {"purchases": reversed(purchases), "sum_bills": sum_bills, "username":username, "form":form})

    def post(self, request, username):
        list_of_subs = [sub.sub for sub in SubSellerSubset.objects.filter(head__username=username)]
        list_of_subs.append(User.objects.get(username=username))
        purchases = PurchaseRecord.objects.filter(created_for__in=list_of_subs).order_by("date_time")
        sum_bills = sum(p.price if p.type in [0,1] else p.price * -1 for p in purchases)
        form = PriceForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            PurchaseRecord.objects.create(
                created_for = User.objects.get(username=username),
                created_by = request.user,
                service_name = "پرداخت",
                price = cd["price"] * 1000,
                type = 2,
                description =  "پرداخت",
                date_time = datetime.now().timestamp(),
            ).save()
            return redirect("finance:sellers_pay_bill", username)
        return render(request, 'seller_pay_page.html',
                      {"purchases": reversed(purchases), "sum_bills": sum_bills, "username": username, "form":form})

class SelectSeller(LoginRequiredMixin, View):
    def get(self, request, action):
        if request.user.level_access == 1:
            sellers_list = [row.sub for row in SubSellerSubset.objects.filter(head=request.user)]
        else:
            sellers_list = [row for row in User.objects.filter(level_access__in=[0,1])]
        return render(request, "subsellers_list_finance.html", {"sellers_list": sellers_list, "action": action})



class SellersShowPrices(LoginRequiredMixin, View):
    def get(self, request, username):
        list_of_subs = [sub.sub for sub in SubSellerSubset.objects.filter(head__username=username)]
        list_of_subs.append(User.objects.get(username=username))
        price_model = SellersPrices.objects.filter(seller__in=list_of_subs).order_by("seller_id",'expire_limit', 'usage_limit')
        return render(request, 'sellers_show_prices.html', {'price_model': price_model, "username":username})



class SellersDeletePrice(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        model_obj = SellersPrices.objects.get(id=obj_id)
        model_obj.delete()
        messages.success(request, "تعرفه با موفقیت حذف شد.")
        return redirect('finance:sellers_show_prices', model_obj.seller.username)



class SellersAddPrice(LoginRequiredMixin, View):
    def get(self, request, username):
        form = SellersAddPriceForm(username=username)
        return render(request, 'seller_add_price.html', {'form': form, "username":username})

    def post(self, request, username):
        form = SellersAddPriceForm(request.POST, username=username)
        if form.is_valid():
            cd = form.cleaned_data
            if cd["type_conf"] == "limited":
                usage = cd["usage"]
                month = cd["month"]
                ip_limit = 0
            elif cd["type_conf"] == "inf_usage":
                usage = 0
                month = cd['month']
                ip_limit = cd["ip_limit"]
            elif cd["type_conf"] == "inf_time":
                usage = cd["usage"]
                month = 0
                ip_limit = 0
            price = cd["price"] * 1000

            SellersPrices.objects.create(
                seller=User.objects.get(username=username),
                price=price,
                expire_limit=int(month),
                user_limit=int(ip_limit),
                usage_limit=int(usage),
            ).save()
            return redirect('finance:sellers_show_prices', username)
        return render(request, 'seller_add_price.html', {'form': form, "username":username})


class SellerDeletePayBills(LoginRequiredMixin, View):
    def get(self, request, id):
        PurchaseRecord.objects.get(id=id).delete()
        return redirect(request.META.get('HTTP_REFERER', '/'))
