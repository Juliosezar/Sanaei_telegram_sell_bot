from django.db import models
from django.db.models import PositiveIntegerField


class Server(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    url = models.URLField()
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    inbound_id = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)
    maximum_connection = PositiveIntegerField(default=0)
    online_users = PositiveIntegerField(default=0)
    last_update = models.BigIntegerField(default=0)
    config_example = models.TextField(default='')
    copy_in_link = models.BooleanField(default=True)

