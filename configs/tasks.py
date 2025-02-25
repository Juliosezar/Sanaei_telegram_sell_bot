import json
from celery import shared_task
from django.conf import settings
from zipfile import ZipFile

from bot.commands import CommandRunner
from finance.models import BotPayment
from servers.models import Server
from .models import ConfigJobsQueue, Config, Service, EndNotif
from servers.sanaie_api import ServerApi
from datetime import datetime
from logs.views import LogAction
import os

@shared_task
def run_jobs():
    for job_queue in ConfigJobsQueue.objects.filter(done=False, config__server__active=True):
        response = False
        if job_queue.job == 0: # create
            response = ServerApi.create_config(job_queue.config.server.id, job_queue.config.service.name, job_queue.config.service.uuid)
            if response:
                status = Config.objects.get(configjobsqueue=job_queue)
                status.status = 1
                status.save()

        elif job_queue.job == 1: # disable
            response = ServerApi.disable_config(job_queue.config.server.id, job_queue.config.service.uuid, False)
        elif job_queue.job == 2: # delete
            response = ServerApi.delete_config(job_queue.config.server.id, job_queue.config.service.uuid)
            if response:
                job_queue.config.status = 3
                job_queue.config.save()
        elif job_queue.job == 3: # enable
            response = ServerApi.disable_config(job_queue.config.server.id, job_queue.config.service.uuid, True)
        elif job_queue.job == 4: # reset
            response = ServerApi.reset_usage(job_queue.config.server.id, job_queue.config.service.name)


        if response:
            job_queue.done = True

        job_queue.last_try = datetime.now().timestamp()
        job_queue.try_count += 1
        job_queue.save()

@shared_task
def update_usage():
    for server in Server.objects.filter(active=True):
        response = ServerApi.get_list_configs(server.id)
        try:
            if response:
                for name in response:
                    config_uuid = (response[name]["uuid"])
                    if Config.objects.filter(service__uuid=config_uuid, server=server, status__in=[1,2]).exists():
                        config_obj = Config.objects.get(service__uuid=config_uuid, server=server)
                        config_obj.usage = response[name]["usage"]
                        if response[name]["enable"]:
                            config_obj.status = 1
                        else:
                            config_obj.status = 2
                        config_obj.last_update = datetime.now().timestamp()
                        if config_obj.service.status == 0 and not response[name]["enable"]:
                            r = ServerApi.disable_config(server.id, config_obj.service.uuid, True)
                            if r:
                                LogAction.create_celery_log(config_obj.service.owner, f"✅ Enable / service \'{config_obj.service.name}\' / server \'{server.name}\'", config_obj.service.customer, 4)
                        elif config_obj.service.status in [1,2] and response[name]["enable"]:
                            r = ServerApi.disable_config(server.id, config_obj.service.uuid, False)
                            if r:
                                LogAction.create_celery_log(config_obj.service.owner, f"⛔ Disable / service \'{config_obj.service.name}\' / server \'{server.name}\'", config_obj.service.customer,5)
                        elif config_obj.service.status == 4:
                            delete = ServerApi.delete_config(server.id, config_obj.service.uuid)
                            if delete:
                                config_obj.status = 3
                                LogAction.create_celery_log(config_obj.service.owner, f"❌ Delete / service \'{config_obj.service.name}\' / server \'{server.name}\'", config_obj.service.customer,3)
                        config_obj.save()
                server.last_update = datetime.now().timestamp()
                server.save()
            else:
                pass  # Todo: send not working notif
        except Exception as e:
            print(e) # TODO: log error
        response2 = ServerApi.get_online_users(server.id)
        if response2:
            server.online_users = response2
            server.save()


@shared_task
def sum_usage_and_ending_services():
    for service in Service.objects.all():
        service.usage = sum([config.usage for config in Config.objects.filter(service=service)])
        if not service.status in [4, 1]:
            status = 0
            if service.usage >= service.usage_limit and not service.usage_limit == 0:
                status = 2
            if not service.expire_time == 0:
                if service.expire_time < datetime.now().timestamp() and not service.start_time == 0:
                    status = 2
            if service.status != status:
                service.status = status
        service.save()


@shared_task
def delete_service():
    for service in Service.objects.filter(status=4):
        deleted = True
        for config in Config.objects.filter(service=service):
            if not config.status == 3:
                deleted = False
        if deleted:
            if service.customer:
                CommandRunner.send_msg(service.customer.chat_id, f" ❌ سرویس {service.name} حذف شد.")
            LogAction.create_celery_log(service.owner, f"❌ delete completely ❌ /  service \'{service.name}\'", service.customer, 0)
            service.delete()



@shared_task
def delete_not_recorded_config():
    for server in Server.objects.filter(active=True):
        response = ServerApi.get_list_configs(server.id)
        if response:
            for name in response:
                config_uuid = (response[name]["uuid"])
                if not Service.objects.filter(uuid=config_uuid).exists():
                    ServerApi.delete_config(server.id, config_uuid)


@shared_task
def create_recorded_configs():
    for server in Server.objects.filter(active=True):
        response = ServerApi.get_list_configs(server.id)
        if response:
            list_uuid = []
            for config in response:
                list_uuid.append(config)
            for config in Config.objects.filter(server=server, status__in=[1,2]):
                if (not config.service.name in list_uuid ) and config.service.status != 4:
                    res = ServerApi.create_config(server.id, config.service.name, config.service.uuid)
                    if res:
                        LogAction.create_celery_log(config.service.owner,
                                                    f"+ create / service \'{config.service.name}\' / server \'{server.name}\'",
                                                    config.service.customer, 1)


@shared_task
def send_end_service_notif():
    for service in Service.objects.filter(owner=None, status__in=[0,1,2]):
        if service.customer:
            if service.status == 2:
                if not EndNotif.objects.filter(service=service, type=0).exists():
                    CommandRunner.send_end_of_config_notif(service.uuid, 0)
                    EndNotif.objects.create(service=service, type=0, timestamp=datetime.now().timestamp()).save()


            elif service.status in [0,1]:
                if service.start_time != 0 and (service.expire_time - datetime.now().timestamp()) < 43400 and service.expire_time != 0:
                    if not EndNotif.objects.filter(service=service, type=1).exists():
                        CommandRunner.send_end_of_config_notif(service.uuid, 1)
                        EndNotif.objects.create(service=service, type=1, timestamp=datetime.now().timestamp()).save()

                if (service.usage_limit - service.usage) < 0.6 and  service.usage_limit != 0:
                    if not EndNotif.objects.filter(service=service, type=2).exists():
                        CommandRunner.send_end_of_config_notif(service.uuid, 2)
                        EndNotif.objects.create(service=service, type=2, timestamp=datetime.now().timestamp()).save()


@shared_task
def delete_notif():
    for notif in EndNotif.objects.all():
        if (datetime.now().timestamp() - notif.timestamp) > 345600:
            notif.delete()


@shared_task
def auto_delete_service():
    from configs.views import ConfigAction
    for service in Service.objects.filter(status=2):
        if EndNotif.objects.filter(service=service, type=0, service__owner=None).exists():
            if (datetime.now().timestamp() - EndNotif.objects.get(service=service, type=0).timestamp) > 259200:
                if not BotPayment.objects.filter(service_uuid=service.uuid, status__in=[0,1]).exists():
                    ConfigAction.create_config_job_queue(service.uuid,2 ,None)
                    service.status = 4
                    service.save()
                    LogAction.create_celery_log(service.owner, f"🆑 delete sevice by celery ❌ /  service \'{service.name}\'",
                                                service.customer, 2)





@shared_task
def send_back_up():
    source_file_path = settings.BASE_DIR / 'db.sqlite3'
    destination_directory = os.environ.get("MEDIA_ROOT") + "/backup/"

    with ZipFile(destination_directory + 'backup.zip', 'w') as zip_file:
        zip_file.write(source_file_path)

    with open(settings.BASE_DIR / 'settings.json', 'r') as f:
        data = json.load(f)
        admins = data["admins_id"]
        for admin in admins:
            with open(destination_directory + "backup.zip", "rb" ) as zip_file:
                data = {
                    "chat_id": admin,
                }
                files = {
                    'document': (os.path.basename(destination_directory + "backup.zip"), zip_file ,'application/octet-stream')
                }
                CommandRunner.send_api("sendDocument",data, files)

