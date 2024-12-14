from celery import shared_task
from .models import ConfigJobsQueue
from servers.sanaie_api import ServerApi
from datetime import datetime

@shared_task
def printer():
    print("Hello World")


@shared_task
def run_jobs():
    for job_queue in ConfigJobsQueue.objects.filter(done=False):
        response = False
        if job_queue.job == 0: # create
            response = ServerApi.create_config(job_queue.config.server.ID, job_queue.config.service.name, job_queue.config.service.uuid)
        elif job_queue.job == 1: # disable
            response = ServerApi.disable_config(job_queue.config.server.ID, job_queue.config.service.uuid, False)
        elif job_queue.job == 2: # delete
            response = ServerApi.delete_config(job_queue.config.server.ID, job_queue.config.service.uuid)
        elif job_queue.job == 3: # enable
            response = ServerApi.disable_config(job_queue.config.server.ID, job_queue.config.service.uuid, True)
        elif job_queue.job == 4: # reset
            response = ServerApi.reset_usage(job_queue.config.server.ID, job_queue.config.service.name)


        if response:
            job_queue.try_count += 1
            job_queue.last_try = datetime.now().timestamp()
            job_queue.done = True
            job_queue.save()