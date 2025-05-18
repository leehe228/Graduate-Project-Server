from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password

from .models import User, File, Chat, Message

import json

# Create your views here.

@csrf_exempt
def health_check(request):
    return JsonResponse({
        "response": 200,
        "message": "server connection sucess",
        "data": None
    })

@csrf_exempt
def register(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        user_id = body.get('user_id')
        user_email = body.get('user_email')
        user_password = body.get('user_password')
        user_name = body.get('user_name')
        user_category = body.get('user_category')
        
        if user_category is None:
            user_category = 0
        
        # 값이 비어있다면 400 오류
        if not user_id or not user_email or not user_password or not user_name \
            or user_id == "" or user_email == "" or user_password == "" or user_name == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
                "data": None
            })
            
        # 이미 존재하는 아이디, 이메일인지 확인
        if User.objects.filter(user_id=user_id).exists():
            return JsonResponse({
                "response": 409,
                "message": "user id already exists",
                "data": None
            })
        
        if User.objects.filter(user_email=user_email).exists():
            return JsonResponse({
                "response": 409,
                "message": "email already exists",
                "data": None
            })
            
        # 비밀번호 암호화
        hashed_password = make_password(user_password)
        
        # User 객체 생성
        user = User(
            user_id=user_id,
            user_email=user_email,
            user_password=hashed_password,
            user_name=user_name,
            user_category=user_category
        )
        
        # User 객체 저장
        user.save()
        
        # 회원가입 성공
        return JsonResponse({
            "response": 200,
            "message": "register success",
            "data": None
        })
        
    else:
        # 잘못된 요청
        return JsonResponse({
            "response": 405,
            "message": "method not allowed",
            "data": None
        })

@csrf_exempt
def login(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        user_id = body.get('user_id')
        user_password = body.get('user_password')
        
        print(user_id, user_password)
        
        # 값이 비어있다면 400 오류
        if not user_id or not user_password or user_id == "" or user_password == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
                "data": None
            })
            
        # 로그인 
        try:
            user = User.objects.get(user_id=user_id)
            
            # 비밀번호 확인
            if check_password(user_password, user.user_password):
                # 로그인 성공
                return JsonResponse({
                    "response": 200,
                    "message": "login success",
                    "data": None
                })
            else:
                # 비밀번호 불일치
                return JsonResponse({
                    "response": 401,
                    "message": "invalid user id or password",
                    "data": None
                })
            
        except User.DoesNotExist:
            return JsonResponse({
                "response": 401,
                "message": "invalid user id or password",
                "data": None
            })
        
    else:
        # 잘못된 요청
        return JsonResponse({
            "response": 405,
            "message": "method not allowed",
            "data": None
        })
