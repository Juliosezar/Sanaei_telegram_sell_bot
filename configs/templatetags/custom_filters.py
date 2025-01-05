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





@register.filter(name="timestamp")
def timestamp(value):
    return JalaliDateTime.fromtimestamp(value, pytz.timezone("Asia/Tehran")).strftime("%c")

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


@register.filter(name="rang")
def rang(num, page):
    if num > 6:
        lt = [1, 2]
        if not page in [1,2,3]:
            print(page)
            print(lt)
            lt.append(-2)
        lt.append(page -1)
        lt.append(page)
        lt.append(page + 1)
        if not page in [num -1,num, num-2, num-3]:
            lt.append(-1)
        lt.append(num - 1)
        lt.append(num)
        for i in lt:
            if i >= num +1:
                lt.remove(i)
            elif i == 0:
                lt.remove(0)
        print(lt)
        lt = list(dict.fromkeys(lt))
        return lt
    else:
        return [i for i in range(1,num+1)]


