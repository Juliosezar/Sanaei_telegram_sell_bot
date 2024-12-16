from django.db import models
from accounts.models import User


class SubSellerSubset(models.Model):
    head = models.ForeignKey(User, on_delete=models.CASCADE, related_name='head')
    sub = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sub')