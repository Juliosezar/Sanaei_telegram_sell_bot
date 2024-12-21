from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .commands import CommandRunner
from customers.models import Customer
from persiantools.jdatetime import JalaliDateTime
import traceback

from .models import CustomerTmpStatus

COMMANDS = {
    '/start': CommandRunner.main_menu,
    'خرید سرویس 🛍': CommandRunner.select_config_expire_time,
    'expire_time': CommandRunner.select_config_usage,
    'usage_limit': CommandRunner.confirm_config_buying,
    'pay_for_config': CommandRunner.pay_for_config,
    "back_to_select_config_expire_time":CommandRunner.back_to_select_config_expire_time,
    'buy_from_wallet': CommandRunner.buy_config_from_wallet,
    # 'abort_buying': CommandRunner.abort_buying,
    'کیف پول 💰': CommandRunner.show_wallet_status,
    # 'تست رایگان 🔥': CommandRunner.test_conf,
    'سرویس های من 🧑‍💻': CommandRunner.my_services,
    'تعرفه ها 💳': CommandRunner.send_prices,
    'ارتباط با ادمین 👤': CommandRunner.contact_us,
    'آیدی من 🆔': CommandRunner.myid,
    # # 'لینک دعوت 📥': CommandRunner.invite_link,
    'down_guid_app': CommandRunner.down_guid_app,
    '💻📱 دانلود اپلیکیشن و راهنمای اتصال 💡': CommandRunner.download_apps,
    "send_guid":CommandRunner.send_guid,
    'add_to_wallet': CommandRunner.set_pay_amount,
    'set_wallet_pay_amount': CommandRunner.send_pay_card_info,
    '❌ لغو پرداخت 💳': CommandRunner.abort,
    'waiting_for_wallet_pic': CommandRunner.get_add_to_wallet_pic,
    "waiting_for_pic_for_buy_config":CommandRunner.get_pic_for_buy_config,
    'service_status': CommandRunner.get_service,
    'renew': CommandRunner.renew_select_config_expire_time,
    'renew2': CommandRunner.renew_select_config_usage,
    'renew3': CommandRunner.renew_confirm_config_buying,
    'renew_wallet': CommandRunner.renew_config_from_wallet,
    "renew_pay": CommandRunner.Renew_pay_for_config,
    "waiting_for_pic_for_renew_config": CommandRunner.get_pic_for_renew_config,

    # "QRcode": CommandRunner.Qrcode
}



'''
    webhook() function recieves bot commands from Telgram Servers
    with POST method and handle what command will run for respons
    to user.
'''


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        try:
            update = json.loads(request.body)
            print(update)
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                if not Customer.objects.filter(chat_id=chat_id).exists():
                    CommandRunner.save_user_info(chat_id)
                # if not Customer.objects.get(userid=chat_id).active:
                #     CommandRunner.send_msg_to_user(chat_id, "🚫 دسترسی شما به بات توسط ادمین لغو شده است.")
                    return JsonResponse({'status': 'ok'})
                if "text" in update["message"]:
                    text: str = update['message']['text']
                    if text in COMMANDS.keys():
                        COMMANDS[text](chat_id)
                    elif  CustomerTmpStatus.objects.get(customer__chat_id=chat_id).status != "normal":
                        COMMANDS[CustomerTmpStatus.objects.get(customer__chat_id=chat_id).status](chat_id, text)
                    elif "/start register_" in text:
                        CommandRunner.register_config(chat_id, text.replace("/start register_", ""))
                    elif "/start off_code_" in text:
                        CommandRunner.active_off_code(chat_id, text.replace("/start off_code_", ""))
                    else:
                        CommandRunner.send_msg(chat_id, "ورودی نامعتبر")
                        CommandRunner.main_menu(chat_id)

                elif "photo" in update["message"]:
                    chat_id = update['message']['chat']['id']
                    status = CustomerTmpStatus.objects.get(customer__chat_id=chat_id).status
                    if status != "normal":
                        file_id = (update["message"]["photo"][-1])["file_id"]
                        COMMANDS[status](chat_id, file_id)
                    # else:
                    #     CommandRunner.send_msg_to_user(chat_id, "ورودی نامعتبر")
                    # COMMANDS["/start"](chat_id)
                return JsonResponse({'status': 'ok'})

            elif 'callback_query' in update:
                msg_id = update["callback_query"]["message"]["message_id"]
                query_data = update['callback_query']['data']
                print(query_data)
                chat_id = update['callback_query']['message']['chat']['id']
                if not Customer.objects.get(chat_id=chat_id).active:
                    CommandRunner.send_msg(chat_id, "🚫 دسترسی شما به بات توسط ادمین لغو شده است.")
                if query_data.split("<~>")[0] in COMMANDS.keys():
                    command = query_data.split("<~>")[0]
                    if "<~>" in query_data:
                        args = query_data.split("<~>")[1]
                        COMMANDS[command](chat_id, msg_id, args)
                    else:
                        COMMANDS[command](chat_id, msg_id)
                else:
                    CommandRunner.send_msg(chat_id, "ورودی نامعتبر")
                    COMMANDS["/start"](chat_id)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print(e)
            error_str = traceback.format_exc()
            # ErrorLog.objects.create(error=str(error_str), timestamp=int(JalaliDateTime.now().timestamp())).save()
            return JsonResponse({'status': 'Connection refused'})
    return JsonResponse({'status': 'not a POST request'})
