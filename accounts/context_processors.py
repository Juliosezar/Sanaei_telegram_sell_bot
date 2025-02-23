# myapp/context_processors.py
from os import environ

def global_vars(request):
    return {
        'SITE_NAME': environ.get("SITE_NAME"),
        "LOADING1": environ.get("LOADING1"),
        "LOADING2": environ.get("LOADING2"),
    }