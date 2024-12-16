from celery import shared_task

from servers.models import Server
from .models import ConfigJobsQueue, Config, Service
from servers.sanaie_api import ServerApi
from datetime import datetime



@shared_task
def run_jobs():
    for job_queue in ConfigJobsQueue.objects.filter(done=False):
        response = False
        if job_queue.job == 0: # create
            response = ServerApi.create_config(job_queue.config.server.ID, job_queue.config.service.name, job_queue.config.service.uuid)
            status = Config.objects.get(configjobsqueue=job_queue)
            status.status = 1
            status.save()
        elif job_queue.job == 1: # disable
            response = ServerApi.disable_config(job_queue.config.server.ID, job_queue.config.service.uuid, False)
            print(response)
        elif job_queue.job == 2: # delete
            response = ServerApi.delete_config(job_queue.config.server.ID, job_queue.config.service.uuid)
            if response:
                job_queue.config.status = 3
                job_queue.config.save()
        elif job_queue.job == 3: # enable
            response = ServerApi.disable_config(job_queue.config.server.ID, job_queue.config.service.uuid, True)
            print(response)
        elif job_queue.job == 4: # reset
            response = ServerApi.reset_usage(job_queue.config.server.ID, job_queue.config.service.name)


        if response:
            job_queue.try_count += 1
            job_queue.last_try = datetime.now().timestamp()
            job_queue.done = True
            job_queue.save()


@shared_task
def update_usage():
    for server in Server.objects.all():
        response = ServerApi.get_list_configs(server.ID)
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
                            ServerApi.disable_config(server.ID, config_obj.service.uuid, True)
                        elif config_obj.service.status in [1,2] and response[name]["enable"]:
                            ServerApi.disable_config(server.ID, config_obj.service.uuid, False)
                        elif config_obj.service.status == 4:
                            delete = ServerApi.delete_config(server.ID, config_obj.service.uuid)
                            if delete:
                                config_obj.status = 3
                        config_obj.save()
                server.last_update = datetime.now().timestamp()
                server.save()
        except Exception as e:
            print(e) # TODO: log error

        else:
            pass # Todo: send not working notif

    # sum usages and ended configs
    for service in Service.objects.all():
        service.usage = sum([config.usage for config in Config.objects.filter(service=service)])
        if not service.status in [2,4]:
            if service.usage >= service.usage_limit and not service.usage_limit == 0:
                service.status = 2
            if not service.expire_time == 0 and service.expire_time < datetime.now().timestamp() and not service.start_time == 0:
                service.status = 2
            service.save()


@shared_task
def delete_service():
    for service in Service.objects.filter(status=4):
        deleted = True
        for config in Config.objects.filter(service=service):
            if not config.status == 3:
                deleted = False
        if deleted:
            service.delete()


@shared_task
def delete_not_recorded_config():
    for server in Server.objects.all():
        response = ServerApi.get_list_configs(server.ID)
        if response:
            for name in response:
                config_uuid = (response[name]["uuid"])
                if not Service.objects.filter(uuid=config_uuid).exists():
                    ServerApi.delete_config(server.ID, config_uuid)


@shared_task
def create_recorded_configs():
    for server in Server.objects.all():
        response = ServerApi.get_list_configs(server.ID)
        if response:
            list_uuid = []
            for config in response:
                list_uuid.append(response[config]["uuid"])

            for config in Config.objects.filter(server=server, status__in=[1,2]):
                if not config.service.uuid in list_uuid and not config.service.status == 4:
                    ServerApi.create_config(server.ID, config.service.name, config.service.uuid)