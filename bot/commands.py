import os
import uuid
from datetime import datetime
from os import environ
from configs.models import Service
from customers.models import Customer
import requests
import json
from .models import CustomerTmpStatus, SendMessage
from finance.models import BotPayment, Prices, UserActiveOffCodes, OffCodes
from django.core.files.base import ContentFile
from django.conf import settings
import urllib.parse
from uuid import UUID
import qrcode


TOKEN = environ.get('TELEGRAM_TOKEN')
TELEGRAM_SERVER_URL = f"https://api.telegram.org/bot{TOKEN}/"

class Action:

    @staticmethod
    def change_customer_bot_tmp_stat(chat_id, status, values=None):
        if values is None:
            values = {}
        stat = CustomerTmpStatus.objects.get(customer__chat_id=chat_id)
        stat.status = status
        stat.values = values
        stat.save()

    @staticmethod
    def args_spliter(text):
        return text.split("<%>")

    @staticmethod
    def is_valid_uuid(uuid_to_test):
        try:
            uuid_obj = UUID(uuid_to_test, version=4)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

class CommandRunner:

    @classmethod
    def send_api(cls, api_method, data, file=False):
        url = TELEGRAM_SERVER_URL + api_method
        try:
            if not file:
                response = requests.post(url, json=data, timeout=3)
            else:
                response = requests.post(url, data=data, timeout=3, files=file)
            print(response.json())
            return response
        except requests.exceptions.RequestException as e:
            print(e)
            # ErrorLog.objects.create(
            #     error=e,
            #     timestamp=int(JalaliDateTime.now().timestamp())
            # )
            return False
        # TODO : log error

    @classmethod
    def save_user_info(cls, chat_id, *args):
        data = {'chat_id': chat_id}
        info = CommandRunner.send_api("getChat", data)
        info = info.json()
        if "username" in info["result"]:
            username = info["result"]["username"]
        else:
            username = None

        if "first_name" in info["result"]:
            first_name = info["result"]["first_name"]
        else:
            first_name = ""
        print(data)
        Customer.objects.create(
            chat_id=chat_id,
            username=username,
            name=first_name,
        ).save()
        CustomerTmpStatus.objects.create(
            customer=Customer.objects.get(chat_id=chat_id),
        ).save()
        cls.send_msg(chat_id, f"به بات {environ.get('SITE_NAME')} خوش آمدید :)")
        cls.main_menu(chat_id)
        return {"username": username, "first_name": first_name}

    @classmethod
    def send_msg(cls, chat_id, msg, keyboard=False):
        for i in ['_', '*', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            msg = msg.replace(i, f"\\{i}")
        data = {'chat_id': chat_id,
                'text': msg,
                'parse_mode': 'MarkdownV2',
                }
        if keyboard:
            data['reply_markup'] = {"inline_keyboard": [keyboard]}
        respons = cls.send_api("sendMessage", data)
        if respons:
            return True
        return False


    @classmethod
    def download_photo(cls, file_id, chat_id):
        file_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()["result"]
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info['file_path']}"
        img = requests.get(file_url)
        if img.status_code == 200:
            img_data = img.content
            count = BotPayment.objects.filter(customer__chat_id=chat_id, status=-1)
            if count.count() > 1:
                counter = 0
                for obj in count:
                    counter += 1
                    if counter == count.count():
                        break
                    obj.delete()
            cpq_obj = BotPayment.objects.get(customer__chat_id=chat_id, status=-1)
            cpq_obj.image.save(file_id + ".jpg", ContentFile(img_data), save=False)
            cpq_obj.status = 0
            cpq_obj.save()
            return True
        return False


    @classmethod
    def main_menu(cls, chat_id, *args):
        Action.change_customer_bot_tmp_stat(chat_id, "normal")

        data = {
            'chat_id': chat_id,
            'text': '🏠 منوی اصلی 🏠',
            'reply_markup': {
                'keyboard': [
                    [{'text': 'خرید سرویس 🛍'}],
                    [{'text': 'سرویس های من 🧑‍💻'}],
                    [{'text': 'ارتباط با ادمین 👤'}],
                    [{'text': 'تست رایگان 🔥'}, {'text': 'کیف پول 💰'}],
                    [{'text': 'تعرفه ها 💳'}, {'text': 'آیدی من 🆔'}],
                    [{'text': '💻📱 دانلود اپلیکیشن و راهنمای اتصال 💡'}],
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'is_persistent': False,
            }
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def abort(cls, chat_id, *args):
        cls.send_msg(chat_id, "❌ عملیات لغو شد.❗️")
        cls.main_menu(chat_id)

    @classmethod
    def show_wallet_status(cls, chat_id, *args):
        amount = Customer.objects.get(chat_id=chat_id).wallet
        amount = f"{amount:,}"
        data = {
            'chat_id': chat_id,
            'text': f' 🟢 موجودی کیف پول شما : \n\n💵 *{amount}* تومان ',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '➕ افزایش موجودی 💲', 'callback_data': 'add_to_wallet<~>'}],
                ]
            },
            'parse_mode': 'Markdown',
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def set_pay_amount(cls, chat_id, *args):
        print(65644)
        status = CustomerTmpStatus.objects.get(customer__chat_id=chat_id)
        status.status = "set_wallet_pay_amount"
        status.save()
        data = {
            'chat_id': chat_id,
            "text": "مبلغ مورد نظر را خود را به تومان وارد کنید :",
            'reply_markup': {
                'keyboard': [
                    [{'text': '❌ لغو پرداخت 💳'}],
                ],
                'resize_keyboard': True,
                'one_time_keyboard': True,
            }
        }
        cls.send_api("sendMessage", data)


    @classmethod
    def send_pay_card_info(cls, chat_id, *args):
        amount = args[0]
        if amount.isnumeric():
            amount = int(amount)
            if 2000 <= amount < 1000000:
                with open(settings.BASE_DIR / 'settings.json', 'r') as f:
                    data = json.load(f)
                    card_num = data["pay_card_number"]
                    card_name = data["pay_card_name"]
                data = {
                    'chat_id': chat_id,
                    'text': f" مبلغ {amount}تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
                    'parse_mode': 'Markdown',
                }
                Action.change_customer_bot_tmp_stat(chat_id,"waiting_for_wallet_pic", {"price":amount})
                cls.send_api("sendMessage", data)
            else:
                cls.send_msg(chat_id, "حداقل مقدار پرداختی 2000 تومان است. دوباره وارد کنید :")
        else:
            cls.send_msg(chat_id, "مقدار را به صورت لاتین(انگلیسی) و به تومان وارد کنید :")


    @classmethod
    def get_add_to_wallet_pic(cls, chat_id, file_id,*args):
        customer_temp = CustomerTmpStatus.objects.get(customer__chat_id=chat_id, status="waiting_for_wallet_pic")
        price = customer_temp.values["price"]
        BotPayment.objects.create(
            customer=Customer.objects.get(chat_id=chat_id),
            price=price,
            action=0,
            status=-1
        ).save()
        if cls.download_photo(file_id, chat_id):
            cls.send_msg(chat_id,"پرداخت شما ثبت شد. \n لطفا منتظر باشید تا پرداخت شما توسط ادمین تایید شود.")
            cls.main_menu(chat_id)
        else:
            cls.send_msg(chat_id, "مشکل در دریافت تصویر / لطفا دقایقی دیگر دوباره امتحان کنید.")
            BotPayment.objects.get(customer=Customer.objects.get(chat_id=chat_id),status=-1).delete()


    @classmethod
    def contact_us(cls, chat_id, *args):
        data = {
            'chat_id': chat_id,
            'text': f' با سلام خدمت شما کاربر گرامی \n\n' + "🟢 پشتیبانی از 8 صبح تا 12 شب 👇\n" + f"🆔 {environ.get("ADMIN_USERNAME")}"
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def myid(cls, chat_id, *args):
        cls.send_msg(chat_id, '👤 آیدی شما : \n ' f'🆔 `{chat_id}`')


    @classmethod
    def download_apps(cls, chat_id, *args):
        with open(settings.BASE_DIR/ "settings.json") as f:
            f_data = json.load(f)["applicatios"]
            keybord = []
            for ind,app in enumerate(f_data):
                keybord.append([{"text":app["app_name"], "callback_data": f"down_guid_app<~>{ind}"}])

        data = {
            'chat_id': chat_id,
            'text': '🏻📥 لیست نرم افزار ها به شرح زیر است. متانسب با سیستم عامل خود انتخاب کنید. 👇',
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': keybord
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def down_guid_app(cls, chat_id, *args):
        print(args)
        msg_id = int(args[0])
        ind = int(args[1])
        print(ind)
        with open(settings.BASE_DIR/ "settings.json") as f:
            f_data = json.load(f)["applicatios"]

        data = {
            'chat_id': chat_id,
            "message_id": msg_id,
            'text': f'{f_data[ind]["app_name"]}' "\n\n" '📥 دانلود / 💡 آموزش استفاده از برنامه 👇' ,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '📥 لینک دانلود برنامه 📥','url': f_data[ind]["download_url"]}],
                    [{'text': '💡 آموزش برنامه 💡', 'callback_data': f"send_guid<~>{f_data[ind]["guid"]}"}],
                ]
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def send_guid(cls, chat_id, *args):
        ind = int(args[1])
        data = {
            'chat_id': chat_id,
            'from_chat_id': environ.get("SIDE_CHANNEL_USERNAME"),
            'message_id': ind
        }
        cls.send_api("copyMessage", data)

    @classmethod
    def send_prices(cls, chat_id, *args):
        with open(settings.BASE_DIR / 'settings.json', 'r') as f:
            data = json.load(f)
            msg_id = data["prices_msg_id"]

        data = {
            'chat_id': chat_id,
            'from_chat_id': environ.get("SIDE_CHANNEL_USERNAME"),
            'message_id': msg_id
        }
        cls.send_api("copyMessage", data)


    @classmethod
    def select_config_expire_time(cls, chat_id, *args):
        price_obj = Prices.objects.all()
        print(price_obj)
        months = list(set([m.expire_limit for m in price_obj]))
        month_list = []
        for m in months:
            if m == 0:
                m_text = " ♾ " + "زمان نامحدود"
            else:
                m_text = " 🔘 " + f"{m} ماهه"
            month_list.append([{'text': f"{m_text}", 'callback_data': f"expire_time<~>{m}"}])
        print(month_list)
        data = {
            'chat_id': chat_id,
            'text':  '⏱ مدت زمان سرویس خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard': month_list
            },
        }
        cls.send_api("sendMessage", data)

    @classmethod
    def back_to_select_config_expire_time(cls, chat_id, *args):
        price_obj = Prices.objects.all()
        msg_id = int(args[0])
        print(price_obj)
        months = list(set([m.expire_limit for m in price_obj]))
        month_list = []
        for m in months:
            if m == 0:
                m_text = " ♾ " + "زمان نامحدود"
            else:
                m_text = " 🔘 " + f"{m} ماهه"
            month_list.append([{'text': f"{m_text}", 'callback_data': f"expire_time<~>{m}"}])
        print(month_list)
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text':  '⏱ مدت زمان سرویس خود را انتخاب کنید 👇🏻',
            'reply_markup': {
                'inline_keyboard': month_list
            },
        }
        cls.send_api("editMessageText", data)

    @classmethod
    def select_config_usage(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        expire_month = int(arg_splited[0])
        price_obj = Prices.objects.filter(expire_limit=expire_month)
        usage_list = []
        for u in price_obj:
            if u.usage_limit == 0:
                u_text = " ♾ " + "نامحدود" + " - " + f"{u.user_limit} کاربره" + " - " + f"{u.price} تومان "
            else:
                u_text = " 🔘 " + f"{u.usage_limit} گیگ" + " - " + f"{u.price} تومان "
            usage_list.append([{'text': u_text,
                                'callback_data': f"usage_limit<~>{expire_month}<%>{u.usage_limit}<%>{u.user_limit}"}])
        usage_list.append([{'text': '🔙 بازگشت', 'callback_data': f"back_to_select_config_expire_time"}])

        if expire_month == 0:
            choosen = " زمان نامحدود ♾ "
        else:
            choosen = f" {expire_month} ماهه"

        text =  f' ⏱ انقضا: {choosen}\n\n' + '🔃 حجم کانفیگ خود را انتخاب کنید 👇🏻'
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text': text,
            'reply_markup': {
                'inline_keyboard': usage_list
            },
        }
        cls.send_api("editMessageText", data)


    @classmethod
    def confirm_config_buying(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        expire_month = int(arg_splited[0])
        usage_limit = int(arg_splited[1])
        user_limit = int(arg_splited[2])
        custumer_obj = Customer.objects.get(chat_id=chat_id)
        wallet_amount = custumer_obj.wallet
        price = Prices.objects.get(expire_limit=expire_month, user_limit=user_limit, usage_limit=usage_limit).price
        wallet_amount_text = f"{wallet_amount:,}"
        have_off_code = False
        text = ""
        if expire_month == 0:
            expire_month_text = " زمان نامحدود ♾"
            if UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_infinit_times=True).exists():
                have_off_code = True
        else:
            expire_month_text = f" {expire_month} ماهه"
        if usage_limit == 0:
            usage_limit_text = ' نامحدود ♾'
            if UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False,off_code__for_infinit_usages=True).exists():
                have_off_code = True
        else:
            usage_limit_text = f'{usage_limit} GB'

        if usage_limit != 0 and expire_month != 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id,
                                                                    used=False, off_code__for_not_infinity=True).exists():
            have_off_code = True

        if user_limit == 0:
            user_limit_text = ' بدون محدودیت ♾'
        else:
            user_limit_text = user_limit

        if have_off_code:
            text = "🟢 کد تخفیف شما صورت گرفت و از هزینه سرویس کم گردید." "\n\n"
            off_model = UserActiveOffCodes.objects.get(custumer__chat_id=chat_id, used=False)
            if off_model.off_code.type_off:
                price = price - int(off_model.off_code.amount * price / 100)
            else:
                price = price - (off_model.off_code.amount * 1000)
        price_text = f"{price:,}"
        pay_amount = price - wallet_amount
        pay_amount_text = f"{pay_amount:,}"
        if wallet_amount >= price:

            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text':text  + f' ⏱ انقضا: {expire_month_text}\n'
                                                        f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                                                                                                                                         f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {price_text}'
                        + f' تومان از کیف پول شما کسر خواهد شد.\n تایید خرید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': [[{'text': '✅ تایید خرید 💳',
                                          'callback_data': f'buy_from_wallet<~>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                        [{"text": '🔙 بازگشت',
                                          'callback_data': f"expire_time<~>{expire_month}"}],
                                        [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                },
            }
        else:
            if wallet_amount == 0:
                text_pay = f'کاربر گرامی، برای فعال سازی این سرویس مبلغ {pay_amount_text}'
            else:
                text_pay = f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {pay_amount_text}'
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': text + f' ⏱ انقضا: {expire_month_text}\n'
                                                               f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                        + text_pay + f' تومان را پرداخت کنید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': [[{'text': '✅ پرداخت / کارت به کارت 💳',
                                          'callback_data': f'pay_for_config<~>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                        [{"text": '🔙 بازگشت',
                                          'callback_data': f"expire_time<~>{expire_month}"}],
                                        [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                },
            }
        cls.send_api("editMessageText", data)


    @classmethod
    def pay_for_config(cls, chat_id, *args):
        msg_id = args[0]
        arg_splited = Action.args_spliter(args[1])
        expire_limit = int(arg_splited[0])
        usage_limit = int(arg_splited[1])
        user_limit = int(arg_splited[2])
        price_obj = Prices.objects.get(usage_limit=usage_limit, expire_limit=expire_limit, user_limit=user_limit)
        price = price_obj.price
        have_off_code = False
        if usage_limit != 0 and expire_limit != 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_not_infinity=True).exists():
            have_off_code = True
        elif usage_limit == 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_infinit_usages=True).exists():
            have_off_code = True
        elif expire_limit == 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_infinit_times=True).exists():
            have_off_code = True
        if have_off_code:
            off_model = UserActiveOffCodes.objects.get(custumer__chat_id=chat_id, used=False)
            if off_model.off_code.type_off:
                price = price - int(off_model.off_code.amount * price / 100)
            else:
                price = price - (off_model.off_code.amount * 1000)
        wallet = Customer.objects.get(chat_id=chat_id).wallet
        with open(settings.BASE_DIR / 'settings.json', 'r') as f:
            data = json.load(f)
            card_num = data["pay_card_number"]
            card_name = data["pay_card_name"]
        data = {
            'message_id': msg_id,
            'chat_id': chat_id,
            'text': f" مبلغ {price - wallet} تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
            'parse_mode': 'Markdown',
        }
        data2 = {
            'chat_id': chat_id,
            "text": "تصویر پرداختی خود را ارسال کنید :",
            'resize_keyboard': True,
            'one_time_keyboard': True,
            'reply_markup': {
                'keyboard': [
                    [{'text': '❌ لغو پرداخت 💳'}]]
            },
        }
        Action.change_customer_bot_tmp_stat(chat_id, "waiting_for_pic_for_buy_config", {"price_obj_id": price_obj.id})

        # expire limit * 30
        cls.send_api("sendMessage", data2)
        cls.send_api("editMessageText", data)

    @classmethod
    def get_pic_for_buy_config(cls, chat_id, file_id,*args):
        customer_temp = CustomerTmpStatus.objects.get(customer__chat_id=chat_id, status="waiting_for_pic_for_buy_config")
        price_obj = Prices.objects.get(id=customer_temp.values["price_obj_id"])
        customer = Customer.objects.get(chat_id=chat_id)
        BotPayment.objects.create(
            customer=customer,
            price=price_obj.price - customer.wallet,
            action=1,
            info={"config_price":price_obj.price, "usage_limit":price_obj.usage_limit, "expire_time":price_obj.expire_limit, "user_limit":price_obj.user_limit},
            status=-1
        ).save()
        if cls.download_photo(file_id, chat_id):
            cls.send_msg(chat_id,"پرداخت شما ثبت شد. \n لطفا منتظر باشید تا پرداخت شما توسط ادمین تایید شود.")
            cls.main_menu(chat_id)
        else:
            cls.send_msg(chat_id, "مشکل در دریافت تصویر")
            BotPayment.objects.get(customer=Customer.objects.get(chat_id=chat_id),status=-1).delete()

    @classmethod
    def send_sub_link(cls, config_uuid):
        service = Service.objects.get(uuid=config_uuid)
        sub_link_domain = environ.get("SUB_LINK_DOMAIN")
        sub_link_domain = "https://" + sub_link_domain.replace("https://","").replace("http://","")
        sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{config_uuid}/")
        send_text = (f" 🔰 سرویس: {service.name}"  "\n\n" ' 🌐 لینک سرویس: \n\n  '+ sub_link + "\n" + "لینک بالا را کپی کرده و در برنامه مورد نظر اضافه کنید." + "\n" + "برای دریافت Qrcode و نمایش حجم و زمان باقی مانده میتوانید روی لینک کلیک کنید یا به بخش <<سرویس های من>> در منوی بات مراجعه کنید.")
        cls.send_msg(service.customer.chat_id, send_text)



    @classmethod
    def my_services(cls, chat_id, *args):
        services = Service.objects.filter(customer__chat_id=chat_id)
        opts = []
        for service in services:
            opts.append([{'text': " 🔗 " + service.name ,'callback_data': f'service_status<~>{service.uuid}'}])
        data = {
            'chat_id': chat_id,
            'text': '🌐 سرویس های شما 👇🏻',
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': opts

            },
        }
        if services.count() == 0:
            data = {
                'chat_id': chat_id,
                'text': 'شما سرویس ثبت شده ای ندارید.',
                'parse_mode': 'Markdown',
            }

        if args:
            msg_id = int(args[0])
            data["message_id"] = msg_id
            cls.send_api("editMessageText", data)
        else:
            cls.send_api("sendMessage", data)



    @classmethod
    def get_service(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        conf_uuid = arg_splited[0]
        keybord = []
        if Service.objects.filter(uuid=conf_uuid).exists():
            keybord.append([{'text': '🔄 Refresh 🔄', 'callback_data': f'service_status<~>{conf_uuid}'}])
            service = Service.objects.get(uuid=conf_uuid, status__in=[0,1,2
                                                                      ])
            text = '🔰 نام سرویس: ' + f'{service.name}' '\n'
            sub_link_domain = environ.get("SUB_LINK_DOMAIN")
            sub_link_domain = "https://" + sub_link_domain.replace("https://", "").replace("http://", "")
            sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{conf_uuid}/")

            kind = "حجمی"
            usage_limit = service.usage_limit
            if usage_limit == 0:
                kind = "حجم نامحدود"
                usage_limit = "♾"
            elif service.expire_time == 0:
                usage_limit = str(service.usage_limit) + "GB"
                kind = "حجمی / زمان نامحدود"
            if service.expire_time == 0:
                expire_days = "♾"
            elif service.status == 2:
                expire_days = "اتمام اشتراک ❌"
            else:
                if service.start_time == 0:
                    expire_days = f" {service.expire_time} روز"
                else:
                    now = datetime.now().timestamp()
                    value = (service.expire_time - now) / 86400
                    hour = int((abs(value) % 1) * 24)
                    day = abs(int(value))
                    expire_days = f" {day} روز" f' و {hour} ساعت '
            if service.start_time == 0:
                status = "استارت نشده 🔵"

            elif service.status == 0:
                status = "فعال 🟢"

            else:
                status = "تماما شده 🔴"
                keybord.append([{'text': '♻️ تمدید ♻️', 'callback_data': f'tamdid<~>{conf_uuid}'}])
            text += '\n' "📥 حجم مصرفی: " f'{service.usage}GB از {usage_limit}' '\n' '⏳ روز های باقی مانده: ' f'{expire_days}' '\n' '📶 وضعیت: ' f'{status}' '\n' f'⚙️ نوع: ' f'{kind}'
            text = text.replace('_', "\\_")
            text += ("\n\n"'📡 کانفیگ شما:' ' 'f"\n`{sub_link}`\n\n")
            text +=  "❇️ برای کپی کانفیگ بر روی متن ⬆️ کلیک کنید." "\n"
            text += "\n" " برای آپدیت اطلاعات بالا بر روی دکمه (Refresh) کلیک کنید 👇"
        else:
            text = '❌ این سرویس دیگر فعال نیست.'

        keybord.append([{'text': 'دریافت QRCode', 'callback_data': f"QRcode<~>{conf_uuid}"}])
        keybord.append([{'text': '🔙 بازگشت', 'callback_data': f"سرویس های من 🧑‍💻"}])
        data = {
            'chat_id': chat_id,
            'message_id': msg_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': keybord
            },
        }
        cls.send_api("editMessageText", data)

    @classmethod
    def register_config(cls, chat_id, msg):
        if Action.is_valid_uuid(msg):
            if Service.objects.filter(uuid=msg).exists():
                custumer = Customer.objects.get(chat_id=chat_id)
                obj = Service.objects.get(uuid=msg)
                obj.customer = custumer
                obj.save()
                sub_link_domain = environ.get("SUB_LINK_DOMAIN")
                sub_link_domain = "https://" + sub_link_domain.replace("https://", "").replace("http://", "")
                sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{msg}/")
                text = f" نام سرویس: {obj.name}" + "\n\n" + f"`{sub_link}`\n\n" +  "❇️ برای کپی کانفیگ بر روی متن ⬆️ کلیک کنید."
                text = text.replace("_", "\\_")
                cls.send_msg(chat_id, "🟢 سرویس شما ثبت شد.")
                data = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'Markdown',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': 'دریافت QRcode',
                                              'callback_data': f'QRcode<~>{msg}'}],
                                            ]

                    },
                }
                cls.send_api("sendMessage", data)
            else:
                cls.send_msg(chat_id, "سرویسی با این مشخصات ثبت نشده است.")
        else:
            cls.send_msg(chat_id, 'لینک نامعتبر است.')
    @classmethod
    def active_off_code(cls, chat_id, *args):
        off_uuid = args[0]
        if Action.is_valid_uuid(off_uuid):
            if OffCodes.objects.filter(uid=off_uuid).exists():
                off_model = OffCodes.objects.get(uid=off_uuid)
                if off_model.end_timestamp > int(datetime.now().timestamp()):
                    if UserActiveOffCodes.objects.filter(off_code=off_model, custumer__chat_id=chat_id).exists():
                        active_code_model = UserActiveOffCodes.objects.get(off_code=off_model, custumer__chat_id=chat_id)
                        if active_code_model.used and active_code_model.off_code.use_count == 1:
                            cls.send_msg(chat_id, "🔴 شما فقط یکبار میتوانید این کد تخفیف را فعال کنید.")
                        elif not active_code_model.used and active_code_model.off_code.use_count == 1:
                            cls.send_msg(chat_id,
                                                 "🟠 این کدتخفیف قبلا برای شما فعال شده است. دربخش پرداخت هزینه (خرید یا تمدید سرویس) بصورت خودکار برایتان محاسبه میگردد.")
                        elif active_code_model.used and active_code_model.off_code.use_count == 0:
                            if UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False).exists():
                                obj = UserActiveOffCodes.objects.get(custumer__chat_id=chat_id, used=False)
                                obj.used = True
                                obj.save()
                            active_code_model.used = False
                            active_code_model.save()

                            cls.send_msg(chat_id, "🟢 این کدتخفیف دوباره برای شما فعال گردید.")
                        elif not active_code_model.used and active_code_model.off_code.use_count == 0:
                            cls.send_msg(chat_id,
                                                 "🟠 این کد از قبل برای شما فعال است.  دربخش پرداخت هزینه (خرید یا تمدید سرویس) بصورت خودکار برایتان محاسبه میگردد.")
                    else:
                        if UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False).exists():
                            UserActiveOffCodes.objects.get(custumer__chat_id=chat_id, used=False).delete()
                        UserActiveOffCodes.objects.create(off_code=off_model,
                                                          custumer=Customer.objects.get(chat_id=chat_id)).save()
                        cls.send_msg(chat_id,
                                             "🟢 کد تخفیف برای شما فعال گردید. هنگام خرید یا تمدید سرویس به صورت خودکار (در مرحله پرداخت) برای شما محاسبه میگردد.")

                else:
                    cls.send_msg(chat_id, "🔴 مهلت فعال کردن این کد تخفیف گذشته است.")
            else:
                cls.send_msg(chat_id, "🔴 کد تخفیفی با این مشخصات یافت نشد.")
        else:
            cls.send_msg(chat_id, "🔴 لینک کد تخفیف اشتباه است.")


    @classmethod
    def send_end_of_config_notif(cls, service_uuid, type_, *args):
        service = Service.objects.get(uuid=service_uuid)
        if type_ == 0:
            text = "‼️ مشتری گرامی، اشتراک سرویس زیر به اتمام رسیده است.🔔 \n\n"

        elif type_ == 1:
            text = "🔶 مشتری گرامی، کمتر از 12 ساعت تا اتمام سرویس شما باقی مانده است، برای جلوگیری از قطع شدن سرویس خود آنرا تمدید کنید.🔔 \n\n"
        else:
            text = "🔶 مشتری گرامی، کمتر از 0.5 گیگ (500مگابایت) از سرویس شما باقی مانده است، برای جلوگیری از قطع شدن سرویس خود آنرا تمدید کنید.🔔 \n\n"

        text += '🔰 نام سرویس: ' + f'{service.name}' '\n'
        kind = "حجمی"
        usage_limit = service.usage_limit
        if usage_limit == 0:
            kind = "حجم نامحدود"
            usage_limit = "♾"
        elif service.expire_time == 0:
            usage_limit = str(service.usage_limit) + "GB"
            kind = "حجمی / زمان نامحدود"
        if service.expire_time == 0:
            expire_days = "♾"
        elif service.status == 2:
            expire_days = "اتمام اشتراک ❌"
        else:
            if service.start_time == 0:
                expire_days = f" {service.expire_time} روز"
            else:
                now = datetime.now().timestamp()
                value = (service.expire_time - now) / 86400
                hour = int((abs(value) % 1) * 24)
                day = abs(int(value))
                expire_days = f" {day} روز" f' و {hour} ساعت '
        if service.start_time == 0:
            status = "استارت نشده 🔵"

        elif service.status == 0:
            status = "فعال 🟢"

        else:
            status = "تماما شده 🔴"

        text += '\n' "📥 حجم مصرفی: " f'{service.usage}GB از {usage_limit}' '\n' '⏳ روز های باقی مانده: ' f'{expire_days}' '\n' '📶 وضعیت: ' f'{status}' '\n' f'⚙️ نوع: ' f'{kind}'
        text += "\n\n" "✅ برای تمدید سرویس بر روی دکمه (تمدید) کلیک کنید 👇"
        text = text.replace('_', "\\_")

        text = text.replace('_', "\\_")
        data = {
            'chat_id': service.customer.chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '♻️ تمدید ♻️', 'callback_data': f'renew<~>{service_uuid}'}], ]
            },
        }
        cls.send_api("sendMessage", data)



    @classmethod
    def renew_select_config_expire_time(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        config_uuid = arg_splited[0]
        if Service.objects.filter(uuid=config_uuid).exists():
            service_name = Service.objects.get(uuid=config_uuid).name
            price_obj = Prices.objects.all()
            months = list(set([m.expire_limit for m in price_obj]))
            month_list = []
            for m in months:
                if m == 0:
                    m_text = " ♾ " + "زمان نامحدود"
                else:
                    m_text = " 🔘 " + f"{m} ماهه"
                month_list.append([{'text': f"{m_text}", 'callback_data': f"renew2<~>{config_uuid}<%>{m}"}])
            print(month_list)
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': '🔰 تمدید سرویس: ' f'{service_name}' '\n' '⏱ مدت زمان سرویس خود را انتخاب کنید 👇🏻',
                'reply_markup': {
                    'inline_keyboard': month_list
                },
            }
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': 'این سرویس لغو گردیده است.',
            }
        cls.send_api("editMessageText", data)



    @classmethod
    def renew_select_config_usage(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        config_uuid = arg_splited[0]
        expire_month = int(arg_splited[1])
        if Service.objects.filter(uuid=config_uuid).exists():
            service_name = Service.objects.get(uuid=config_uuid).name
            price_obj = Prices.objects.filter(expire_limit=expire_month)
            usage_list = []
            for u in price_obj:
                if u.usage_limit == 0:
                    u_text = " ♾ " + "نامحدود" + " - " + f"{u.user_limit} کاربره" + " - " + f"{u.price} تومان "
                else:
                    u_text = " 🔘 " + f"{u.usage_limit} گیگ" + " - " + f"{u.price} تومان "
                usage_list.append([{'text': u_text,
                                    'callback_data': f"renew3<~>{config_uuid}<%>{expire_month}<%>{u.usage_limit}<%>{u.user_limit}"}])
            usage_list.append([{'text': '🔙 بازگشت', 'callback_data': f"renew<~>{config_uuid}"}])

            if expire_month == 0:
                choosen = " زمان نامحدود ♾ "
            else:
                choosen = f" {expire_month} ماهه"

            text =  f' ⏱ انقضا: {choosen}\n\n' + '🔃 حجم کانفیگ خود را انتخاب کنید 👇🏻'
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': text,
                'reply_markup': {
                    'inline_keyboard': usage_list
                },
            }
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': 'این سرویس لغو گردیده است.',
            }
        cls.send_api("editMessageText", data)


    @classmethod
    def renew_confirm_config_buying(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        config_uuid = arg_splited[0]
        expire_month = int(arg_splited[1])
        usage_limit = int(arg_splited[2])
        user_limit = int(arg_splited[3])
        if Service.objects.filter(uuid=config_uuid).exists():
            custumer_obj = Customer.objects.get(chat_id=chat_id)
            wallet_amount = custumer_obj.wallet
            price = Prices.objects.get(expire_limit=expire_month, user_limit=user_limit, usage_limit=usage_limit).price
            wallet_amount_text = f"{wallet_amount:,}"
            have_off_code = False
            text = ""
            if expire_month == 0:
                expire_month_text = " زمان نامحدود ♾"
                if UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_infinit_times=True).exists():
                    have_off_code = True
            else:
                expire_month_text = f" {expire_month} ماهه"
            if usage_limit == 0:
                usage_limit_text = ' نامحدود ♾'
                if UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False,off_code__for_infinit_usages=True).exists():
                    have_off_code = True
            else:
                usage_limit_text = f'{usage_limit} GB'

            if usage_limit != 0 and expire_month != 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id,
                                                                        used=False, off_code__for_not_infinity=True).exists():
                have_off_code = True

            if user_limit == 0:
                user_limit_text = ' بدون محدودیت ♾'
            else:
                user_limit_text = user_limit

            if have_off_code:
                text = "🟢 کد تخفیف شما صورت گرفت و از هزینه سرویس کم گردید." "\n\n"
                off_model = UserActiveOffCodes.objects.get(custumer__chat_id=chat_id, used=False)
                if off_model.off_code.type_off:
                    price = price - int(off_model.off_code.amount * price / 100)
                else:
                    price = price - (off_model.off_code.amount * 1000)
            price_text = f"{price:,}"
            pay_amount = price - wallet_amount
            pay_amount_text = f"{pay_amount:,}"
            if wallet_amount >= price:

                data = {
                    'chat_id': chat_id,
                    'message_id': msg_id,
                    'text':text  + f' ⏱ انقضا: {expire_month_text}\n'
                            f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                            f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {price_text}'
                            + f' تومان از کیف پول شما کسر خواهد شد.\n تایید خرید 👇🏻',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': '✅ تایید خرید 💳',
                                              'callback_data': f'renew_wallet<~>{config_uuid}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                            [{"text": '🔙 بازگشت',
                                              'callback_data': f"renew<~>{config_uuid}<%>{expire_month}"}],
                                            [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                    },
                }
            else:
                if wallet_amount == 0:
                    text_pay = f'کاربر گرامی، برای فعال سازی این سرویس مبلغ {pay_amount_text}'
                else:
                    text_pay = f'کاربر گرامی، موجودی کیف پول شما {wallet_amount_text} تومان است، برای فعال سازی این سرویس مبلغ {pay_amount_text}'
                data = {
                    'chat_id': chat_id,
                    'message_id': msg_id,
                    'text': text + f' ⏱ انقضا: {expire_month_text}\n'
                                                                   f' 🔃 حجم : {usage_limit_text} \n' + f' 👤 محدودیت کاربر: {user_limit_text}\n\n' + f' 💵 هزینه سرویس: {price_text} تومان \n\n'
                            + text_pay + f' تومان را پرداخت کنید 👇🏻',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': '✅ پرداخت / کارت به کارت 💳',
                                              'callback_data': f'renew_pay<~>{config_uuid}<%>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
                                            [{"text": '🔙 بازگشت',
                                              'callback_data': f"renew2<~>{config_uuid}<%>{expire_month}"}],
                                            [{'text': 'انصراف ❌', 'callback_data': 'abort_buying'}]]
                    },
                }
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': 'این سرویس لغو گردیده است.',
            }
        cls.send_api("editMessageText", data)


    @classmethod
    def Renew_pay_for_config(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        config_uuid = arg_splited[0]
        expire_limit = int(arg_splited[1])
        usage_limit = int(arg_splited[2])
        user_limit = int(arg_splited[3])
        if Service.objects.filter(uuid=config_uuid).exists():
            price_obj = Prices.objects.get(usage_limit=usage_limit, expire_limit=expire_limit, user_limit=user_limit)
            price = price_obj.price
            have_off_code = False
            if usage_limit != 0 and expire_limit != 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_not_infinity=True).exists():
                have_off_code = True
            elif usage_limit == 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_infinit_usages=True).exists():
                have_off_code = True
            elif expire_limit == 0 and UserActiveOffCodes.objects.filter(custumer__chat_id=chat_id, used=False, off_code__for_infinit_times=True).exists():
                have_off_code = True
            if have_off_code:
                off_model = UserActiveOffCodes.objects.get(custumer__chat_id=chat_id, used=False)
                if off_model.off_code.type_off:
                    price = price - int(off_model.off_code.amount * price / 100)
                else:
                    price = price - (off_model.off_code.amount * 1000)
            wallet = Customer.objects.get(chat_id=chat_id).wallet
            with open(settings.BASE_DIR / 'settings.json', 'r') as f:
                data = json.load(f)
                card_num = data["pay_card_number"]
                card_name = data["pay_card_name"]
            data = {
                'message_id': msg_id,
                'chat_id': chat_id,
                'text': f" مبلغ {price - wallet} تومان را به شماره کارت زیر انتقال دهید، سپس عکس آنرا بعد از همین پیام ارسال نمایید : " + f'\n\n`{card_num}`\n {card_name}',
                'parse_mode': 'Markdown',
            }
            data2 = {
                'chat_id': chat_id,
                "text": "تصویر پرداختی خود را ارسال کنید :",
                'resize_keyboard': True,
                'one_time_keyboard': True,
                'reply_markup': {
                    'keyboard': [
                        [{'text': '❌ لغو پرداخت 💳'}]]
                },
            }
            Action.change_customer_bot_tmp_stat(chat_id, "waiting_for_pic_for_renew_config", {"price_obj_id": price_obj.id, "service_uuid":config_uuid})

            # expire limit * 30
            cls.send_api("sendMessage", data2)
            cls.send_api("editMessageText", data)
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': 'این سرویس لغو گردیده است.',
            }
            cls.send_api("editMessageText", data)


    @classmethod
    def get_pic_for_renew_config(cls, chat_id, file_id,*args):
        customer_temp = CustomerTmpStatus.objects.get(customer__chat_id=chat_id, status="waiting_for_pic_for_renew_config")
        price_obj = Prices.objects.get(id=customer_temp.values["price_obj_id"])
        service = Service.objects.get(uuid=customer_temp.values["service_uuid"])
        BotPayment.objects.create(
            customer=service.customer,
            price=price_obj.price - service.customer.wallet,
            action=2,
            info={"config_price":price_obj.price, "usage_limit":price_obj.usage_limit, "expire_time":price_obj.expire_limit * 30, "user_limit":price_obj.user_limit, "service_uuid":str(service.uuid)},
            status=-1
        ).save()
        if cls.download_photo(file_id, chat_id):
            cls.send_msg(chat_id,"پرداخت شما ثبت شد. \n لطفا منتظر باشید تا پرداخت شما توسط ادمین تایید شود.")
            cls.main_menu(chat_id)
        else:
            cls.send_msg(chat_id, "مشکل در دریافت تصویر")
            BotPayment.objects.get(customer=Customer.objects.get(chat_id=chat_id),status=-1).delete()


    @classmethod
    def renew_config_from_wallet(cls, chat_id, *args):
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        config_uuid = arg_splited[0]
        expire_limit = int(arg_splited[1])
        usage_limit = int(arg_splited[2])
        user_limit = int(arg_splited[3])
        if Service.objects.filter(uuid=config_uuid).exists():
            from finance.views import FinanceAction
            from configs.views import ConfigAction
            from configs.tasks import run_jobs
            service = Service.objects.get(uuid=config_uuid)
            price = Prices.objects.get(usage_limit=usage_limit, expire_limit=expire_limit, user_limit=user_limit).price
            service.usage_limit = usage_limit
            if expire_limit == 0:
                service.expire_time = 0
            else:
                service.expire_time = (datetime.now().timestamp() + (expire_limit * 30 * 86400)) if service.start_time != 0 else expire_limit * 30
            service.expire_time = (datetime.now().timestamp() + (expire_limit * 30 * 86400)) if service.start_time != 0 else expire_limit * 30
            service.user_limit = user_limit
            service.save()
            ConfigAction.create_config_job_queue(service.uuid, 4)
            FinanceAction.change_wallet(price * -1, service.customer.chat_id)
            ConfigAction.reset_config_db(service.uuid)
            run_jobs.delay()
            CommandRunner.send_msg(service.customer.chat_id, f"پرداخت شما تایید و سرویس {service.name} تمدید شد. ✅ ")
            FinanceAction.create_purchase_record(None, None, price, 1,
                                                 f"{usage_limit}GB / {expire_limit * 30}d / {user_limit}u",service.name)

            data = {
                'message_id': msg_id,
                'chat_id': chat_id,
                'text': f"سرویس {service.name} شما تمدید شد و مبلغ {price} تومان از کیف پول شما کسر شد.",
                'parse_mode': 'Markdown',
            }
        else:
            data = {
                'chat_id': chat_id,
                'message_id': msg_id,
                'text': 'این سرویس لغو گردیده است.',
            }
        cls.send_api("editMessageText", data)


    @classmethod
    def buy_config_from_wallet(cls, chat_id, *args):
        from configs.views import ConfigAction
        from finance.views import FinanceAction
        from configs.tasks import run_jobs
        customer = Customer.objects.get(chat_id=chat_id)
        msg_id = int(args[0])
        arg_splited = Action.args_spliter(args[1])
        expire_limit = int(arg_splited[0])
        usage_limit = int(arg_splited[1])
        user_limit = int(arg_splited[2])
        price = Prices.objects.get(usage_limit=usage_limit, expire_limit=expire_limit, user_limit=user_limit).price
        service_uuid = uuid.uuid4()
        service_name = ConfigAction.generate_config_name()
        Service.objects.create(
            uuid=service_uuid,
            name=service_name,
            usage_limit=usage_limit,
            expire_time=expire_limit * 30,
            user_limit=user_limit,
            customer=customer,
        ).save()
        ConfigAction.create_config_db(service_uuid)
        ConfigAction.create_config_job_queue(service_uuid, 0)
        FinanceAction.change_wallet(price * -1, customer.chat_id)
        CommandRunner.send_sub_link(service_uuid)
        run_jobs.delay()
        FinanceAction.create_purchase_record(None, None, price, 0,
                                f"{usage_limit}GB / {expire_limit * 30}d / {user_limit}u",service_name)

        data = {
                'message_id': msg_id,
                'chat_id': chat_id,
                'text': f" مبلغ {price} تومان از کیف پول شما کسر شد.",
                'parse_mode': 'Markdown',
            }
        cls.send_api("editMessageText", data)


    @classmethod
    def Qrcode(cls, chat_id, *args):

        service = Service.objects.get(uuid=args[1])
        sub_link_domain = environ.get("SUB_LINK_DOMAIN")
        sub_link_domain = "https://" + sub_link_domain.replace("https://", "").replace("http://", "")
        sub_link = urllib.parse.urljoin(sub_link_domain, f"/configs/sublink/{args[1]}/")
        img = qrcode.make(sub_link)
        img.save(str(settings.MEDIA_ROOT) + f"/{args[1]}.jpg")
        data = {
            "chat_id": chat_id,
            "caption": service.name,
        }
        with open(str(settings.MEDIA_ROOT) + f"/{args[1]}.jpg", 'rb') as image_file:
            files = {
                'photo': image_file
            }
            CommandRunner.send_api("sendPhoto", data, files)

    @classmethod
    def test_conf(cls, chat_id,*args):
            data = {
                'chat_id': chat_id,
                'text': f'برای دریافت سرویس تست به آی دی زیر پیام دهید: \n\n' + f"🆔 {environ.get("ADMIN_USERNAME")}"
            }
            cls.send_api("sendMessage", data)