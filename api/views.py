from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.

@csrf_exempt
def health_check(request):
    return JsonResponse({
        "response": 200,
        "message": "server connection sucess",
        "data": None
    })
