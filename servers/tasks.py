from datetime import datetime

from bot.commands import CommandRunner
from celery import shared_task
from servers.models import Server
from django.conf import settings
import json

@shared_task
def servers_connection():
    servers = Server.objects.all()
    text = ""
    for server in servers:
        if server.online_users < 4:
            text += f"🔴 {server.name} \n🔴 Problem Connection \n{"➖"*11}\n "
        elif server.online_users < 10:
            text += f"🟠 {server.name} \n🟠 Possible Problem Connection \n{"➖"*11}\n"
        if (datetime.now().timestamp() - server.last_update) > 3600:
            text += f"⭕️ {server.name} \n⭕️ Problem Sanaei Panel connection \n{"➖"*11}\n"
    with open(settings.BASE_DIR / 'settings.json', 'r') as f:
        data = json.load(f)
        admins = data["admins_id"]
        for admin in admins:
            CommandRunner.send_msg(admin, text)