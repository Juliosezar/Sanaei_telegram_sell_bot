from django.db import models
from accounts.models import User
from bot.models import SellerBots

class Seller(models.Model):
    seller = models.OneToOneField(User, on_delete=models.CASCADE)
    bot = models.ForeignKey(SellerBots, on_delete=models.DO_NOTHING, null=True)
    create_access = models.BooleanField(default=False)
    delete_access = models.BooleanField(default=False)
    finance_access = models.BooleanField(default=False)
