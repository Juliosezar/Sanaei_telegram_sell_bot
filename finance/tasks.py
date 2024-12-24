import json

from celery import shared_task
from django.conf import settings

from finance.models import BotPayment


@shared_task
def send_notif_to_admins():
    from bot.commands import CommandRunner
    count = BotPayment.objects.filter(status=0).count()
    if count != 0:
        with open(settings.BASE_DIR / 'settings.json', 'r') as f:
            data = json.load(f)
            admins = data["admins_id"]
            for admin in admins:
                CommandRunner.send_msg(admin, msg=f"{count} پرداخت تایید نشده")