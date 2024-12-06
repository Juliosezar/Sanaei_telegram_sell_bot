from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from .models import BotPayment
from bot.commands import CommandRunner

class Action:
    @staticmethod
    def change_wallet(amount, chat_id):
        pass

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
        if pay_obj.status == 0:
            pass

        #     Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.pay_price)
        #     if model_obj.config_in_queue:
        #         if Customer.objects.get(userid=model_obj.custumer.userid).wallet >= model_obj.config_price:
        #             CommandRunner.send_msg_to_user(model_obj.custumer.userid, "پرداخت شما تایید شد. ✅")
        #             Configs.create_config_from_queue(config_uuid=model_obj.config_uuid)
        #         else:
        #             CommandRunner.send_msg_to_user(model_obj.custumer.userid,
        #                                            f'کابر گرامی مبلغ {model_obj.pay_price} تومان به کیف پول شما اضافه گردید. این مبلغ برای خرید کانفیک مورد نظر کافی نیست. ')
        #     else:
        #         msg = 'پرداخت شما تایید و به کیف پول شما اضافه شد.'
        #         CommandRunner.send_msg_to_user(model_obj.custumer.userid, msg)
        #     model_obj.status = 2
        #     model_obj.timestamp = int(JalaliDateTime.now().timestamp())
        #     model_obj.save()
        #     messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')
        # else:
        #     messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        # return redirect('finance:confirm_payments', 1)


class SecondConfirmPayment(LoginRequiredMixin, View):
    def get(self, request, obj_id):
        pass
        # from connection.command_runer import CommandRunner
        # model_obj = PaymentQueueModel.objects.get(id=obj_id)
        # if model_obj.status == 1:
        #     Wallet.add_to_wallet(model_obj.custumer.userid, model_obj.pay_price)
        #     if model_obj.config_in_queue:
        #         if Customer.objects.get(userid=model_obj.custumer.userid).wallet >= model_obj.config_price:
        #             Configs.create_config_from_queue(config_uuid=model_obj.config_uuid)
        #         else:
        #             CommandRunner.send_msg_to_user(model_obj.custumer.userid,
        #                                            f'کابر گرامی مبلغ {model_obj.pay_price} تومان به کیف پول شما اضافه گردید. این مبلغ برای خرید کانفیک مورد نظر کافی نیست. ')
        #     else:
        #         msg = 'پرداخت شما تایید و به کیف پول شما اضافه شد.'
        #         CommandRunner.send_msg_to_user(model_obj.custumer.userid, msg)
        #     model_obj.status = 3
        #     model_obj.timestamp = int(JalaliDateTime.now().timestamp())
        #     model_obj.save()
        #     messages.success(request, 'پرداخت با موفقیت تایید و به کاربر ارسال شد.')
        #
        # elif model_obj.status == 2:
        #     model_obj.status = 3
        #     model_obj.timestamp = int(JalaliDateTime.now().timestamp())
        #     model_obj.save()
        #     messages.success(request, 'پرداخت با موفقیت تایید شد.')
        #     return redirect('finance:confirm_payments', 2)
        # # ToDO
        # else:
        #     messages.error(request, "این پرداخت توسط ادمین دیگری تایید یا رد شده است.")
        # return redirect('finance:confirm_payments', 2)


class DenyPaymentPage(LoginRequiredMixin, View):
    def get(self, request, obj_id, typ):
        pass

class EditPricePayment(LoginRequiredMixin, View):
    def get(self, request, obj_id, typ):
        pass
    #     form = EditPriceForm
    #     if typ == "buy":
    #         model_obj = PaymentQueueModel.objects.get(id=obj_id)
    #     else:
    #         model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
    #     return render(request, 'edit_price_payment.html', {'obj': model_obj, 'form': form})
    #
    # def post(self, request, obj_id, typ):
    #     form = EditPriceForm(request.POST)
    #     if typ == "buy":
    #         model_obj = PaymentQueueModel.objects.get(id=obj_id)
    #     else:
    #         model_obj = TamdidPaymentQueueModel.objects.get(id=obj_id)
    #     if form.is_valid():
    #         price = form.cleaned_data['price']
    #         model_obj.pay_price = price
    #         model_obj.save()
    #         messages.success(request, "مبلغ با موفقیت تغییر کرد. از لیست زیر آن را تایید کنید.")
    #         return redirect('finance:confirm_payments', 1)
    #     return render(request, 'edit_price_payment.html', {'obj': model_obj, 'form': form})
