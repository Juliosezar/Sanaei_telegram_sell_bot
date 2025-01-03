import uuid

from django import template
# from .models import ConfigsInfo, InfinitCongisLimit
from django.conf import settings
import json
from persiantools.jdatetime import JalaliDateTime
import datetime, pytz

from configs.models import Service

# from servers.models import CreateConfigQueue
# from finance.models import ConfirmPaymentQueue, ConfirmTamdidPaymentQueue

register = template.Library()

with open(settings.BASE_DIR / "settings.json", "r") as f:
    UNLIMIT_LIMIT = json.load(f)["unlimit_limit"]


@register.filter
def price(amount):
    return f"{amount:,}"


@register.filter(name='percent')
def percent_usage(value, arg):
    return int(value / arg * 100)


@register.filter(name="dh")
def day_and_hour(value):
    now = datetime.datetime.now().timestamp()
    value = (value - now) / 86400
    hour = int((abs(value) % 1) * 24)
    day = abs(int(value))
    return f"{day}d  {hour}h"

@register.filter(name="dh_int")
def int_day_and_hour(value):
    now = datetime.datetime.now().timestamp()
    value = (value - now) / 86400
    day = (value)
    return day


# @register.filter(name="break_name")
# def break_name(value):
#     if ConfigsInfo.objects.filter(config_name=value).exists():
#         return f'{value} 🤖'
#     elif '@' in value:
#         return False
#     return value


# @register.filter(name="config_seved")
# def config_seved(value):
#     if ConfigsInfo.objects.filter(config_uuid=value).exists():
#         return True
#     return False


# @register.filter(name="infinit_limit")
# def infinit_limit(value):
#     config_info = ConfigsInfo.objects.filter(config_uuid=value)
#     if config_info.exists():
#         if InfinitCongisLimit.objects.filter(config__config_uuid=value).exists():
#             return InfinitCongisLimit.objects.get(config__config_uuid=value).limit
#         else:
#             return "Not Set"
#     return None


@register.filter(name="timestamp")
def timestamp(value):
    return JalaliDateTime.fromtimestamp(value, pytz.timezone("Asia/Tehran")).strftime("%c")


# @register.filter(name="get_server")
# def get_server(value):
#     if CreateConfigQueue.objects.filter(config_uuid=value).exists():
#         return CreateConfigQueue.objects.get(config_uuid=value).server.server_name
#     else:
#         return "----"


def status(value):
    if value == 1:
        return "waiting for confirm ⏳"
    elif value == 2:
        return "first confirm ☑️"
    elif value == 3:
        return "confirmed ✅"
    else:
        return "Denyed ❌"

@register.filter(name="get_conf_name")
def config_name(uuidd):
    if Service.objects.filter(uuid=uuidd).exists():
        return Service.objects.get(uuid=uuidd).name
    else:
        return "----"


@register.filter(name="split_name")
def split_name(name):
    if "@" in name:
        return name.split("@")[1]
    else:
        return name


# @register.filter(name="paylog")
# def paylog(id: dict):
#     if "buy" in list(id.keys()):
#         obj = ConfirmPaymentQueue.objects.get(id=id["buy"])
#         if obj.config_in_queue:
#             return f"Buy / {config_name(obj.config_uuid)} / {price(obj.pay_price)}T / {status(obj.status)}"
#         else:
#             return f"Wallet / {price(obj.pay_price)}T / {status(obj.status)}"
#     else:
#         obj = ConfirmTamdidPaymentQueue.objects.get(id=id["tamdid"])
#         return f"Tamdid / {obj.config.config_name} / {price(obj.pay_price)}T / {status(obj.status)}"
#
#
# @register.filter(name="get_user")
# def get_user(id: dict):
#     if "buy" in list(id.keys()):
#         obj = ConfirmPaymentQueue.objects.get(id=id["buy"])
#         return obj.custumer.userid
#     else:
#         obj = ConfirmTamdidPaymentQueue.objects.get(id=id["tamdid"])
#         return obj.config.chat_id.userid
