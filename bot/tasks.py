from os import environ
from celery import shared_task
from .models import SendMessage
from .commands import CommandRunner



@shared_task
def send_msg_again():
    counter = 0
    for msg in SendMessage.objects.filter(done=False, try_count__in=[0,1,2]):
        if (msg.updated_at - msg.created_at) < 86400:
            counter += 1
            data = {
                'chat_id': msg.customer.chat_id,
                'from_chat_id': environ.get("SIDE_CHANNEL_USERNAME"),
                'message_id': msg.message_id,
            }
            res = CommandRunner.send_api("copyMessage", data)
            if res:
                msg.done = True
            else:
                msg.try_count += 1
            msg.save()
            if counter == 100:
                break
