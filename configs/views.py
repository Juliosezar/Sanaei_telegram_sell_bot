from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class BotCreateConfigView(LoginRequiredMixin, View):
    def get(self, request, type_):
        pass


class BotListConfigView(LoginRequiredMixin, View):
    def get(self, request):
        pass