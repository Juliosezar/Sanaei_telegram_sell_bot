from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from .forms import EditPayPriceForm, AddPriceForm, AddOffForm
from customers.models import Customer
from .models import BotPayment, OffCodes
from bot.commands import CommandRunner
from persiantools.jdatetime import JalaliDateTime
from .models import Prices
import os
from configs.views import ConfigAction
from configs.models import Service
import uuid
from configs.tasks import run_jobs

class FinanceAction:
    @staticmethod
    def change_wallet(amount, chat_id):
        print(amount)
        customer = Customer.objects.get(chat_id=chat_id)
        customer.wallet = amount + customer.wallet
        customer.save()



class ConfirmPaymentPage(LoginRequiredMixin, View):
    def get(self, request, show_box):
        pay_queue_obj = BotPayment.objects.filter(status=0)
        second_pay_queue_obj = BotPayment.objects.filter(status=1)
        # not_paid_obj = ConfigsInfo.objects.filter(paid=False)
        if not pay_queue_obj.exists() and not second_pay_queue_obj.exists():
            messages.info(request, "پرداختی برای تایید نمانده است. \n برای اطمینان یکبار صفحه را رفرش کنید.")
        return render(request, 'confirm_payment.html',
                      {'confirm': pay_queue_obj, "confirm_count": pay_queue_obj.count(),
                       "second_confirm": second_pay_queue_obj, "second_confirm_count": second_pay_queue_obj.count(),
                       # "not_paid": not_paid_obj, "not_paid_count": not_paid_obj.count(),
                       "show_box": show_box})


class FirstConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        pay_obj = BotPayment.objects.get(id=obj_id)
        print(pay_obj.price)
        FinanceAction.change_wallet(pay_obj.price, pay_obj.customer.chat_id)
        if pay_obj.status == 0:
            if pay_obj.action == 0: # add to wallet
                CommandRunner.send_msg(pay_obj.customer.chat_id, f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد.")
            elif pay_obj.action == 1: # buy service
                CommandRunner.send_msg(pay_obj.customer.chat_id, "پرداخت شما تایید شد. لینک سرویس برای شما ارسال میشود.")
                if Customer.objects.get(chat_id=pay_obj.customer.chat_id).wallet >= pay_obj.info["config_price"]:

                    service_uuid = uuid.uuid4()
                    Service.objects.create(
                        uuid=service_uuid,
                        name=ConfigAction.generate_config_name(),
                        usage_limit=pay_obj.info["usage_limit"],
                        expire_time=pay_obj.info["expre_time"] * 30,
                        user_limit=pay_obj.info["user_limit"],
                        customer=pay_obj.customer,
                    ).save()
                    ConfigAction.create_config_db(service_uuid)
                    ConfigAction.create_config_job_queue(service_uuid, 0)
                    FinanceAction.change_wallet(pay_obj.info["config_price"] * -1, pay_obj.customer.chat_id)
                    CommandRunner.send_sub_link(service_uuid)
                    run_jobs.delay()
                     # TODO: Trigger create config celery
                else:
                    CommandRunner.send_msg(pay_obj.customer.chat_id,
                                           f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد. اما این مبلغ برای خرید کانفیگ انتخابی کافی نیست.")
            elif pay_obj.action == 2: # renew service
                pass # TODO: renew and change wallet

            # pay_obj.status = 1
            # pay_obj.save()
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
                if pay_obj.customer.wallet >= pay_obj.info["config_price"]:
                    service_uuid = uuid.uuid4()
                    Service.objects.create(
                        uuid=service_uuid,
                        name=ConfigAction.generate_config_name(),
                        usage_limit=pay_obj.info["price_obj"],
                        expire_time=pay_obj.info["expre_time"] * 30,
                        user_limit=pay_obj.info["user_limit"],
                        customer=pay_obj.customer,
                    ).save()
                    ConfigAction.create_config_db(service_uuid)
                    ConfigAction.create_config_job_queue(service_uuid, 0)
                      # TODO: Trigger create config celery
                else:
                    CommandRunner.send_msg(pay_obj.customer.chat_id,
                                           f"پرداخت شما تایید شد و به مبلغ {pay_obj.price} تومان به کیف پولتان اضافه شد. اما این مبلغ برای خرید کانفیگ انتخابی کافی نیست.")
            elif pay_obj.action == 2:  # renew service
                pass  # TODO: renew and change wallet

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
        pass

    def post(self, request, obj_id):
        deny_reason = ""
        pay_obj = BotPayment.objects.get(id=obj_id)
        if pay_obj.status == 0:
            CommandRunner.send_msg(pay_obj.customer.chat_id,f"پرداخت شما تایید نشد ❌ \n علت : {deny_reason}")
            pay_obj.status = 9
            pay_obj.save()
        elif pay_obj.action == 1:
            if pay_obj.action == 0:
                pass # TODO:
            elif pay_obj.action == 1:
                pass
            elif pay_obj.action == 5:
                pass
            pay_obj.status = 9
            pay_obj.save()
        else:
            messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        return redirect('finance:confirm_payments', 1)

class EditPricePayment(LoginRequiredMixin, View):
    def get(self, request, obj_id, typ):
        pass
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