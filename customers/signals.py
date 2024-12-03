from venv import create

from .models import Customer
from django.db.models.signals import post_save
from bot.models import CustomerTmpStatus

