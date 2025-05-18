from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password

from .models import User, File, Chat, Message

import json
import os

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create your views here.

@csrf_exempt
def health_check(request):
    return JsonResponse({
        "response": 200,
        "message": "server connection success",
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
        if not (user_id and user_email and user_password and user_name):
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

@csrf_exempt
def get_user(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        
        # 값이 비어있다면 400 오류
        if not user_id or user_id == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
                "data": None
            })
            
        # User 객체 가져오기
        try:
            user = User.objects.get(user_id=user_id)
            
            # User 객체를 JSON 형태로 변환
            user_data = {
                "user_id": user.user_id,
                "user_email": user.user_email,
                "user_name": user.user_name,
                "user_category": user.user_category,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # 성공적으로 가져온 경우
            return JsonResponse({
                "response": 200,
                "message": "request success",
                "data": user_data
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                "response": 404,
                "message": "user id is not found",
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
def upload_file(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        file = request.FILES.get('file')
        
        # 값이 비어있다면 400 오류
        if not user_id or not file or user_id == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
                "data": None
            })
            
        # 파일 크기 확인
        if file.size > MAX_FILE_SIZE:
            return JsonResponse({
                "response": 413,
                "message": "file is too large",
                "data": None
            })
            
        # user id 존재하는지 확인
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "response": 404,
                "message": "user id is not found",
                "data": None
            })
            
        # 파일 저장 경로 설정
        # 파일 경로는 /files/{user_id}/{file_id}.{확장자} 형식으로 저장
        file_path = os.path.join('static/files', user_id)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
            
        # 파일 이름 설정
        file_name = file.name
        file_extension = file_name.split('.')[-1]
        file_id = str(int(File.objects.filter(user_id=user_id).count()) + 1)
        file_name = f"{file_id}.{file_extension}"
        file_path = os.path.join(file_path, file_name)
        
        # 파일 저장
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        print(f"File saved at {file_path}")
                
        # File 객체 생성
        file_obj = File(
            user_id=user,
            file_name=file_name,
            file_path=file_path,
            file_size=file.size
        )
        
        # File 객체 저장
        file_obj.save()
        
        # 파일 업로드 성공
        return JsonResponse({
            "response": 200,
            "message": "file upload success",
            "data": None
        })
    
    else:
        # 잘못된 요청
        return JsonResponse({
            "response": 405,
            "message": "method not allowed",
            "data": None
        })
