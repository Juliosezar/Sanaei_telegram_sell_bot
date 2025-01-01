from django.db import models
from customers.models import Customer
import uuid
from accounts.models import User


class PurchaseRecord(models.Model):
    created_for = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="P_created_for") # null => bot
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="P_created_by") # null => bot
    service_name = models.CharField(max_length=30, null=True)
    price = models.IntegerField(default=0)
    type = models.SmallIntegerField(default=0, choices=[(0,"buy"), (1,"renew"), (2,"pay")])
    description = models.CharField(max_length=120)
    date_time = models.BigIntegerField(default=0)



class BotPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    price = models.IntegerField()
    action = models.IntegerField() # 0 => add wallet / 1 => buy / 2 => renew
    info = models.JSONField(default=dict)
    image = models.ImageField(upload_to='payment_images/', blank=True, null=True)
    status = models.IntegerField()
    service_uuid = models.UUIDField(null=True)
    # -1 waiting for download pic / 0 waiting for firts confirm /
    # 1 first confirm / 2 second confirm / 9 deny confirm


class Prices(models.Model):
    usage_limit = models.PositiveIntegerField()
    expire_limit = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    user_limit = models.PositiveIntegerField(default=0)


class OffCodes(models.Model):
    uid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    type_off = models.BooleanField()  # percent = True / amount = False
    amount = models.PositiveIntegerField()
    customer_count = models.PositiveIntegerField()
    use_count = models.PositiveIntegerField()
    create_timestamp = models.PositiveBigIntegerField()
    end_timestamp = models.PositiveBigIntegerField()
    for_infinit_usages = models.BooleanField()
    for_infinit_times = models.BooleanField()
    for_not_infinity = models.BooleanField()


class UserActiveOffCodes(models.Model):
    off_code = models.ForeignKey(OffCodes, on_delete=models.CASCADE)
    custumer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    used = models.BooleanField(default=False)


######################################################  Sellers


class SellersPrices(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    usage_limit = models.PositiveIntegerField()
    expire_limit = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    user_limit = models.PositiveIntegerField(default=0)
