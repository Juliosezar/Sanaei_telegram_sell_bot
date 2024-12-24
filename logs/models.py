from django.db import models

from accounts.models import User


class CeleryLog(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    timestamp = models.PositiveBigIntegerField()
