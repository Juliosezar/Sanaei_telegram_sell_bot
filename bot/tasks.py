from celery import shared_task
from .models import SendMessage
from .commands import CommandRunner



@shared_task
def send_msg_again():
    for msg in SendMessage.objects.filter(done=False):
        if (msg.updated_at - msg.created_at) < 86400 and msg.try_count < 3:
            CommandRunner.send_msg_again(msg.id)
