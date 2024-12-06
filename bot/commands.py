from os import environ
from customers.models import Customer
import requests
import json
from .models import CustomerTmpStatus
from finance.models import BotPayment, Prices, UserActiveOffCodes
from django.core.files.base import ContentFile
from django.conf import settings



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



class CommandRunner:

    @classmethod
    def send_api(cls, api_method, data):
        url = TELEGRAM_SERVER_URL + api_method
        try:
            # print(data)
            response = requests.post(url, json=data, timeout=3)
            # print(response.json())
            return response
        except requests.exceptions.RequestException as e:
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
        cls.send_msg(chat_id, "به بات NapsV Vpn خوش آمدید :)")
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
        # if not respons:
        #     SendMessage.objects.create(customer=CustumerModel.objects.get(chat_id=chat_id), message=msg)
        return True

    @classmethod
    def download_photo(cls, file_id, chat_id):
        file_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()["result"]
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info['file_path']}"
        img = requests.get(file_url)
        if img.status_code == 200:
            img_data = img.content
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
            'text': f' با سلام خدمت شما کاربر گرامی \n\n' + "🟢 پشتیبانی از 8 صبح تا 12 شب 👇\n" + "🆔 @NapsV_supp"
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
                                          'callback_data': f'buy_config_from_wallet<~>{expire_month}<%>{usage_limit}<%>{user_limit}'}],
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
            info={"config_price":price_obj.price, "usage_limit":price_obj.usage_limit, "expre_time":price_obj.expire_limit, "user_limit":price_obj.user_limit},
            status=-1
        ).save()
        if cls.download_photo(file_id, chat_id):
            cls.send_msg(chat_id,"پرداخت شما ثبت شد. \n لطفا منتظر باشید تا پرداخت شما توسط ادمین تایید شود.")
            cls.main_menu(chat_id)
        else:
            cls.send_msg(chat_id, "مشکل در دریافت تصویر")
            BotPayment.objects.get(customer=Customer.objects.get(chat_id=chat_id),status=-1).delete()
