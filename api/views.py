from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.utils import timezone
import logging

from .utils import file_to_sqlite, execute_sqlite_query, run_pyplot_code
from .backend import langchain, text2sql, make_title
from .models import User, File, Chat, Message
from . import utils

import threading
import json
import os
import uuid
import time
import re
import pandas as pd
from pathlib import Path

from langchain_openai.chat_models import ChatOpenAI

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

model = ChatOpenAI(
    model="gpt-4o-2024-08-06",
    temperature=0.0,
)

# 모델 최대 호출 횟수
MAX_ITER = 6
DATE_RE  = re.compile(r"{{\s*(get_\w+)\((.*?)\)\s*}}")    # 자리표시자 패턴

def _eval_date_placeholder(expr: str) -> str:
    """`{{get_date(...)}}` · `{{get_weekdate(...)}}` → ISO-8601 문자열"""
    fn_name, arg_str = DATE_RE.match(expr).groups()
    kwargs = {}
    if arg_str.strip():
        for kv in arg_str.split(','):
            k, v = kv.split('=')
            kwargs[k.strip()] = int(v)
    return getattr(utils, fn_name)(**kwargs) 

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SYSTEM_PROMPTS: dict[str, str] = {}

for md_file in PROMPT_DIR.glob("*.md"):
    SYSTEM_PROMPTS[md_file.stem] = md_file.read_text(encoding='utf-8')

assert SYSTEM_PROMPTS, "No system prompts found in the prompts directory."
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info(f"[api.views] Loaded {len(SYSTEM_PROMPTS)} system prompts: {', '.join(SYSTEM_PROMPTS.keys())}")

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

def _background_file_processing(file_id: int):
    try:
        start_time = time.time()
        file = File.objects.get(file_id=file_id)
        file_path = file.file_path
        
        file.file_processed = file.FileProcessingStatus.PROCESSING
        file.save()
        
        base, _ = os.path.splitext(file_path)
        dest = f"{base}.db"
        
        db_path, schema_text = file_to_sqlite(
            file_path=file_path,
            db_path=dest,
            if_exists='replace',
            chunksize=1000
        )
        
        file.file_sqlpath = db_path
        file.file_schema = schema_text
        file.file_processed = file.FileProcessingStatus.COMPLETED
        file.save()
        
        end_time = time.time()
        print(f"File processing completed in {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        file = File.objects.get(file_id=file_id)
        
        if file:
            file.file_processed = file.FileProcessingStatus.FAILED
            file.file_error = f"{e}"
            file.save()
            
            print(f"File processing failed\n\n{e}")
            
        else:
            print(f"file id {file_id} is not found")
        

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        file = request.FILES.get('file')
        file_category = request.POST.get('category', 'default')
        
        # 값이 비어있다면 400 오류
        if not user_id or not file or user_id == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
                "data": None
            })
            
        # category가 올바른지 확인
        if file_category not in ['default', 'cafe', 'cvs']:
            return JsonResponse({
                "response": 400,
                "message": "invalid file category",
                "data": None
            })
            
        # 파일이 csv, xls, xlsx 확장자인지 확인
        if not (file.name.endswith('.csv') or file.name.endswith('.xls') or file.name.endswith('.xlsx')):
            return JsonResponse({
                "response": 415,
                "message": "unsupported file type",
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
        original_file_name = file.name
        file_extension = original_file_name.split('.')[-1]
        file_id = str(uuid.uuid4())
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
            file_name=original_file_name,
            file_path=file_path,
            file_size=file.size,
            file_type=file_extension,
            file_business_category=file_category,
        )
        
        # File 객체 저장
        file_obj.save()
        
        # 파일 처리 스레드 시작
        threading.Thread(
            target=_background_file_processing,
            args=(file_obj.file_id,),
            daemon=True
        ).start()
        
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

@csrf_exempt
def list_files(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        
        # 값이 비어있다면 400 오류
        if not user_id or user_id == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
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
            
        # File 객체 가져오기
        files = File.objects.filter(user_id=user)
        
        # File 객체를 JSON 형태로 변환
        file_list = []
        for file in files:
            file_processed_bool = (file.FileProcessingStatus.COMPLETED == file.file_processed)
            
            file_data = {
                "file_id": file.file_id,
                "file_name": file.file_name,
                "file_size_kb": file.file_size // 1024,
                "file_size_b": file.file_size,
                "file_type": file.file_type,
                "file_path": file.file_path,
                "file_processed": file_processed_bool,
                "file_error": file.file_error,
                "created_at": file.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "file_business_category": file.file_business_category,
            }
            file_list.append(file_data)
        
        # 성공적으로 가져온 경우
        return JsonResponse({
            "response": 200,
            "message": "request success",
            "data": file_list
        })
        
    else:
        # 잘못된 요청
        return JsonResponse({
            "response": 405,
            "message": "method not allowed",
            "data": None
        })

@csrf_exempt
def delete_file(request):
    if request.method == 'DELETE':
        file_id = request.GET.get('file_id')
        
        # 값이 비어있다면 400 오류
        if not file_id or file_id == "":
            return JsonResponse({
                "response": 400,
                "message": "missing required fields",
                "data": None
            })
            
        # File 객체 가져오기
        try:
            file = File.objects.get(file_id=file_id)
        except File.DoesNotExist:
            return JsonResponse({
                "response": 404,
                "message": "file id is not found",
                "data": None
            })
            
        # 실제 파일 삭제
        try:
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
            
        try:
            if os.path.exists(file.file_sqlpath):
                os.remove(file.file_sqlpath)
        except Exception as e:
            print(f"Error deleting SQL file: {e}")
            
        # File 객체 삭제
        file.delete()
        
        # 파일 삭제 성공
        return JsonResponse({
            "response": 200,
            "message": "file delete success",
            "data": None
        })
        
    else:
        # 잘못된 요청
        return JsonResponse({
            "response": 405,
            "message": "method not allowed",
            "data": None
        })


def _record_error(chat: Chat, prev_msgs: list, image_url: str | None, err: Exception, label: str):
    """에러를 assistant role 로 저장하고 history 리스트도 갱신."""
    msg_txt = f"[ERROR/{label}] {err}"
    # history에 추가 ― 다음 turn 에 LLM이 참고할 수 있음
    prev_msgs.append({"role": "assistant", "content": msg_txt})
    # DB에도 저장 (ASSISTANT 역할, 이미지 링크 유지)
    Message.objects.create(
        chat_id=chat,
        message_text=msg_txt,
        message_role=Message.MessageRole.ASSISTANT,
        message_image_url=image_url
    )
    return msg_txt


@csrf_exempt
def start_chat(request: WSGIRequest) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({"response": 405,
                             "message": "method not allowed",
                             "data": None})

    body          = json.loads(request.body)
    user_id       = body.get('user_id')
    user_question = (body.get('message_text') or "").strip()
    sel_file_id   = body.get('file_id')              # 선택 파일 ID

    if not user_id or not user_question:
        return JsonResponse({"response": 400,
                             "message": "missing required fields",
                             "data": None})

    # 0) 사용자 확인
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"response": 404,
                             "message": "user id is not found",
                             "data": None})

    # 1) Chat 및 첫 User Message
    with transaction.atomic(): 
        chat = Chat.objects.create(user_id=user)
        chat.chat_title = make_title(model=model, message=user_question) or "새 대화"

        target_file: File | None = None
        if sel_file_id is not None:
            try:
                target_file = File.objects.get(file_id=sel_file_id,
                                               user_id=user,
                                               file_processed=File.FileProcessingStatus.COMPLETED)
                chat.file_id = target_file
            except File.DoesNotExist:
                return JsonResponse({"response": 404,
                                     "message": "file id is not found or not processed",
                                     "data": None})
        chat.save()

        Message.objects.create(chat_id=chat,
                               message_text=user_question,
                               message_role=Message.MessageRole.USER)

    # user prompt에 schema 추가
    if target_file is not None:
        user_question = f"file의 db schema:\n{target_file.file_schema}\n\n{user_question}"

    # 2) 대화 컨텍스트
    # 선택한 파일 카테고리에 따라 시스템 프롬프트를 결정
    if target_file is not None:
        cat = target_file.file_business_category
    else:
        cat = "default"
    
    system_prompt = SYSTEM_PROMPTS.get(cat, SYSTEM_PROMPTS['default'])
    
    prev_msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_question}
    ]

    assistant_final = ""
    image_url: str | None = None
    turn = 0
    need_more = True

    print(f"[Chat {chat.chat_id}] Start. Question: {user_question}")

    # 3) 대화 루프
    while need_more and turn < MAX_ITER:
        turn += 1
        print(f"[Chat {chat.chat_id}] === LLM TURN {turn}/{MAX_ITER} ===")

        assistant_reply = langchain(model,
                                    system_prompt,
                                    prev_msgs[1:],          # system 제외
                                    prev_msgs[-1]["content"])
        print(f"[Chat {chat.chat_id}] LLM raw ↴\n{assistant_reply}\n")

        # ── 날짜 자리표시자 치환 ───────────────────────────────
        for ph in DATE_RE.findall(assistant_reply):
            full = "{{" + ph[0] + "(" + ph[1] + ")}}"
            assistant_reply = assistant_reply.replace(
                full, _eval_date_placeholder(full))

        internal_log = [f"TURN {turn} RAW\n{assistant_reply}"]

        # ── [T2S] 분기 ───────────────────────────────────────
        if assistant_reply.startswith("[T2S]"):
            if target_file is None:
                try:
                    target_file = File.objects.filter(
                        user_id=user, file_processed=File.FileProcessingStatus.COMPLETED).latest('updated_at')
                except File.DoesNotExist:
                    assistant_final = "처리된 파일이 없습니다. 데이터를 먼저 업로드해 주세요."
                    break

            sql_query = text2sql(model, user_question, target_file.file_schema)
            internal_log.append(f"\nSQL:\n{sql_query}")

            try:
                result = execute_sqlite_query(target_file.file_sqlpath, sql_query, True)
            except Exception as e:
                assistant_final = _record_error(chat, prev_msgs, image_url, e, "SQL")
                need_more = False
                break
            
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    assistant_final = "SQL 쿼리 결과가 없습니다."
                    break
                preview = result.head(5).to_markdown(index=False)
                
            elif isinstance(result, list):
                if not result:
                    assistant_final = "SQL 쿼리 결과가 없습니다."
                    break
                tmp_df = pd.DataFrame(result, columns=[f"c{i+1}" for i in range(len(result[0]))])
                preview = tmp_df.head(5).to_markdown(index=False)
                
            elif isinstance(result, int):
                preview = f"{result:,} row(s) affected."
                
            else:   # pd.Series 등 예외적인 타입 대비
                preview = str(result)[:500]
            
            internal_log.append(f"\nResult preview:\n{preview}")

            prev_msgs.append({"role": "assistant",
                              "content": f"```sql\n{sql_query}\n```\n{preview}"})
            Message.objects.create(chat_id=chat,
                                   message_text="\n".join(internal_log),
                                   message_role=Message.MessageRole.INTERNAL,
                                   message_image_url=image_url)
            continue

        # ── [PLOT] 분기 ─────────────────────────────────────
        if assistant_reply.startswith("[PLOT]"):
            m = re.search(r"```python\s*(.*?)\s*```", assistant_reply, re.S | re.I)
            if not m:
                assistant_final = "그래프 코드를 읽을 수 없습니다."
                break
            py_code = m.group(1)

            img_dir = Path(f"media/{user_id}/{chat.chat_id}")
            img_dir.mkdir(parents=True, exist_ok=True) 
            img_path = img_dir / f"{uuid.uuid4()}.png" 

            try:
                run_pyplot_code(py_code, img_path)
                image_url = "/" + str(img_path)
            except Exception as e:
                assistant_final = _record_error(chat, prev_msgs, image_url, e, "PLOT")
                need_more = False
                break
                
            internal_log.append(f"\nPlot saved → {image_url}")

            prev_msgs.append({"role": "assistant",
                              "content": f"Plot saved at {image_url}"})
            Message.objects.create(chat_id=chat,
                                   message_text="\n".join(internal_log),
                                   message_role=Message.MessageRole.INTERNAL,
                                   message_image_url=image_url)
            continue

        # ── <ASK_USER> 즉시 반환 ────────────────────────────
        if assistant_reply.rstrip().endswith("<ASK_USER>"):
            assistant_final = assistant_reply.replace("<ASK_USER>", "").strip()
            Message.objects.create(chat_id=chat,
                                   message_text=assistant_reply,
                                   message_role=Message.MessageRole.ASSISTANT,
                                   message_image_url=image_url)
            need_more = False
            break

        # ── 최종 답변 또는 추가 질문 ─────────────────────────
        if "<REQUEST_INFO>" in assistant_reply and turn < MAX_ITER:
            prev_msgs.append({"role": "assistant", "content": assistant_reply})
            Message.objects.create(chat_id=chat,
                                   message_text=assistant_reply,
                                   message_role=Message.MessageRole.ASSISTANT,
                                   message_image_url=image_url)
            continue

        assistant_final = assistant_reply.replace("<END>", "").strip()
        Message.objects.create(chat_id=chat,
                               message_text=assistant_final,
                               message_role=Message.MessageRole.ASSISTANT,
                               message_image_url=image_url)
        need_more = False

    # 4) 자동 종료 알림
    if turn >= MAX_ITER and need_more:
        assistant_final += "\n(대화가 길어 자동 종료되었습니다.)"

    print(f"[Chat {chat.chat_id}] Finished after {turn} turn(s).")

    return JsonResponse({
        "response": 200,
        "message": "chat creation success",
        "data": {
            "chat_id":   chat.chat_id,
            "chat_title": chat.chat_title,
            "response":  assistant_final,
            "image_url": image_url
        }
    })

@csrf_exempt
def query_chat(request: WSGIRequest) -> JsonResponse:
    """
    기존 채팅방에 메시지를 추가 전송하고 GPT-4o 응답을 받아온다.
    요청 JSON: { "chat_id": <int>, "message_text": <str> }
    """
    if request.method != "POST":
        return JsonResponse({"response": 405, "message": "method not allowed", "data": None})

    try:
        body = json.loads(request.body)
        chat_id = body.get("chat_id")
        user_input = (body.get("message_text") or "").strip()
    except Exception:
        return JsonResponse({"response": 400, "message": "invalid body", "data": None})

    if not chat_id or not user_input:
        return JsonResponse({"response": 400, "message": "missing required fields", "data": None})

    # ── 0. Chat / User 확인 ───────────────────────────────────
    try:
        chat = Chat.objects.select_related("user_id", "file_id").get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return JsonResponse({"response": 404, "message": "chat id is not found", "data": None})

    user = chat.user_id
    target_file: File | None = chat.file_id      # may be None

    # ── 1. User 메시지 저장 ───────────────────────────────────
    Message.objects.create(chat_id=chat,
                           message_text=user_input,
                           message_role=Message.MessageRole.USER)

    # ── 2. 이전 대화 기록 로드 (System + 모든 Assistant/User) ──
    history = (Message.objects
               .filter(chat_id=chat)
               .exclude(message_role=Message.MessageRole.INTERNAL)
               .order_by("created_at"))

    # 선택한 파일 카테고리에 따라 시스템 프롬프트를 결정
    if target_file is not None:
        cat = target_file.file_business_category
    else:
        cat = "default"
        
    system_prompt = SYSTEM_PROMPTS.get(cat, SYSTEM_PROMPTS['default'])
    prev_msgs = [{"role": "system", "content": system_prompt}]
                 
    for m in history:
        role = "assistant" if m.message_role == Message.MessageRole.ASSISTANT else "user"
        prev_msgs.append({"role": role, "content": m.message_text})

    # ── 3. 최신 질문 반영 (schema prefix 포함) ────────────────
    augmented_question = user_input
    if target_file is not None:
        augmented_question = f"file의 db schema:\n{target_file.file_schema}\n\n{user_input}"
    prev_msgs[-1]["content"] = augmented_question   # 마지막 user 메시지 대체

    # ── 4. LLM ↔ 파이프라인 (start_chat 루프 재활용) ─────────
    assistant_final = ""
    image_url: str | None = None
    need_more, turn = True, 0

    while need_more and turn < MAX_ITER:
        turn += 1
        print(f"[Chat {chat.chat_id}] === QUERY TURN {turn}/{MAX_ITER} ===")

        assistant_reply = langchain(model,
                                    system_prompt,
                                    prev_msgs[1:],         # system 제외
                                    prev_msgs[-1]["content"])
        print(f"[Chat {chat.chat_id}] LLM raw ↴\n{assistant_reply}\n")

        # 날짜 자리표시자 치환
        for ph in DATE_RE.findall(assistant_reply):
            full = "{{" + ph[0] + "(" + ph[1] + ")}}"
            assistant_reply = assistant_reply.replace(full, _eval_date_placeholder(full))

        # ── 분기 처리 (T2S / PLOT / ASK_USER / 종료) ──────────
        if assistant_reply.startswith("[T2S]"):
            if target_file is None:
                try:
                    target_file = File.objects.filter(user_id=user,
                                                      file_processed=File.FileProcessingStatus.COMPLETED).latest("updated_at")
                except File.DoesNotExist:
                    assistant_final = "처리된 파일이 없습니다. 데이터를 먼저 업로드해 주세요."
                    break

            sql_query = text2sql(model, user_input, target_file.file_schema)
            try:
                result = execute_sqlite_query(target_file.file_sqlpath, sql_query, True)
            except Exception as e:
                assistant_final = f"SQL 실행 오류: {e}"
                break
            
            if isinstance(result, pd.DataFrame):
                if result.empty:
                    assistant_final = "SQL 쿼리 결과가 없습니다."
                    break
                preview = result.head(5).to_markdown(index=False)

            elif isinstance(result, list):
                if not result:
                    assistant_final = "SQL 쿼리 결과가 없습니다."
                    break
                
                tmp_df = pd.DataFrame(result, columns=[f"c{i+1}" for i in range(len(result[0]))])
                preview = tmp_df.head(5).to_markdown(index=False)
                
            elif isinstance(result, int):
                preview = f"{result:,} row(s) affected."
                
            else:
                preview = str(result)[:500]

            prev_msgs.append({"role": "assistant",
                              "content": f"```sql\n{sql_query}\n```\n{preview}"})
            Message.objects.create(chat_id=chat,
                                   message_text=f"[INTERNAL] SQL\n{sql_query}\n{preview}",
                                   message_role=Message.MessageRole.INTERNAL,
                                   message_image_url=image_url)
            continue

        if assistant_reply.startswith("[PLOT]"):
            m = re.search(r"```python\s*(.*?)\s*```", assistant_reply, re.S | re.I)
            if not m:
                assistant_final = "그래프 코드를 읽을 수 없습니다."
                break
            py_code = m.group(1)
            img_dir = Path(f"media/{user.user_id}/{chat.chat_id}")
            img_dir.mkdir(parents=True, exist_ok=True)
            img_path = img_dir / f"{uuid.uuid4()}.png"
            
            try:
                run_pyplot_code(py_code, img_path)
                image_url = "/" + str(img_path)
            except Exception as e:
                assistant_final = _record_error(chat, prev_msgs, image_url, e, "PLOT")
                need_more = False
                break

            prev_msgs.append({"role": "assistant",
                              "content": f"Plot saved at {image_url}"})
            Message.objects.create(chat_id=chat,
                                   message_text=f"[INTERNAL] Plot saved → {image_url}",
                                   message_role=Message.MessageRole.INTERNAL,
                                   message_image_url=image_url)
            continue

        if assistant_reply.rstrip().endswith("<ASK_USER>"):
            assistant_final = assistant_reply.replace("<ASK_USER>", "").strip()
            Message.objects.create(chat_id=chat,
                                   message_text=assistant_reply,
                                   message_role=Message.MessageRole.ASSISTANT,
                                   message_image_url=image_url)
            need_more = False
            break

        if "<REQUEST_INFO>" in assistant_reply and turn < MAX_ITER:
            prev_msgs.append({"role": "assistant", "content": assistant_reply})
            Message.objects.create(chat_id=chat,
                                   message_text=assistant_reply,
                                   message_role=Message.MessageRole.ASSISTANT,
                                   message_image_url=image_url)
            continue

        assistant_final = assistant_reply.replace("<END>", "").strip()
        Message.objects.create(chat_id=chat,
                               message_text=assistant_final,
                               message_role=Message.MessageRole.ASSISTANT,
                               message_image_url=image_url)
        need_more = False

    if turn >= MAX_ITER and need_more:
        assistant_final += "\n(대화가 길어 자동 종료되었습니다.)"

    return JsonResponse({
        "response": 200,
        "message": "query request success",
        "data": {
            "response": assistant_final,
            "image_url": image_url
        }
    })

@csrf_exempt
def list_chats(request: WSGIRequest) -> JsonResponse:
    """유저의 모든 채팅방 목록 반환"""
    if request.method != "GET":
        return JsonResponse({"response": 405, "message": "method not allowed", "data": None})

    user_id = request.GET.get("user_id")
    if not user_id:
        return JsonResponse({"response": 400, "message": "missing required fields", "data": None})

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"response": 404, "message": "user id is not found", "data": None})

    chats = (Chat.objects.filter(user_id=user)
             .order_by("-updated_at")
             .values("chat_id", "chat_title", "created_at", "updated_at"))

    chat_list = [{
        "chat_id": c["chat_id"],
        "chat_title": c["chat_title"],
        "created_at": c["created_at"].strftime("%Y/%m/%d %H:%M:%S"),
        "updated_at": c["updated_at"].strftime("%Y/%m/%d %H:%M:%S")
    } for c in chats]

    return JsonResponse({"response": 200, "message": "request success",
                         "data": {"chats": chat_list}})


@csrf_exempt
def get_chat_history(request: WSGIRequest) -> JsonResponse:
    """특정 채팅방의 메시지(Internal 제외) 리스트 반환"""
    if request.method != "GET":
        return JsonResponse({"response": 405, "message": "method not allowed", "data": None})

    chat_id = request.GET.get("chat_id")
    if not chat_id:
        return JsonResponse({"response": 400, "message": "missing required fields", "data": None})

    try:
        chat = Chat.objects.get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return JsonResponse({"response": 404, "message": "chat id is not found", "data": None})

    msgs = (Message.objects
            .filter(chat_id=chat)
            .exclude(message_role=Message.MessageRole.INTERNAL)
            .order_by("created_at"))

    msg_list = [{
        "message_id": m.message_id,
        "message_text": m.message_text,
        "message_role": ("assistant" if m.message_role == Message.MessageRole.ASSISTANT else "user"),
        "message_image_url": m.message_image_url,
        "created_at": m.created_at.strftime("%Y/%m/%d %H:%M:%S")
    } for m in msgs]

    return JsonResponse({"response": 200, "message": "request success",
                         "data": {"messages": msg_list}})


@csrf_exempt
def get_chat_history_all(request: WSGIRequest) -> JsonResponse:
    """특정 채팅방의 모든 메시지 리스트 반환"""
    if request.method != "GET":
        return JsonResponse({"response": 405, "message": "method not allowed", "data": None})

    chat_id = request.GET.get("chat_id")
    if not chat_id:
        return JsonResponse({"response": 400, "message": "missing required fields", "data": None})

    try:
        chat = Chat.objects.get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return JsonResponse({"response": 404, "message": "chat id is not found", "data": None})

    msgs = (Message.objects
            .filter(chat_id=chat)
            .order_by("created_at"))
    
    def _message_role_to_str(role):
        if role == Message.MessageRole.ASSISTANT:
            return "assistant"
        elif role == Message.MessageRole.USER:
            return "user"
        else:
            return "internal"

    msg_list = [{
        "message_id": m.message_id,
        "message_text": m.message_text,
        "message_role": _message_role_to_str(m.message_role),
        "message_image_url": m.message_image_url,
        "created_at": m.created_at.strftime("%Y/%m/%d %H:%M:%S")
    } for m in msgs]

    return JsonResponse({"response": 200, "message": "request success",
                         "data": {"messages": msg_list}})
    

@csrf_exempt
def delete_chat(request: WSGIRequest) -> JsonResponse:
    """채팅방 및 하위 메시지·이미지 삭제"""
    if request.method != "DELETE":
        return JsonResponse({"response": 405, "message": "method not allowed", "data": None})

    chat_id = request.GET.get("chat_id")
    if not chat_id:
        return JsonResponse({"response": 400, "message": "missing required fields", "data": None})

    try:
        chat = Chat.objects.get(chat_id=chat_id)
    except Chat.DoesNotExist:
        return JsonResponse({"response": 404, "message": "chat id is not found", "data": None})

    # 연관 이미지 파일도 정리 (media/<user>/<chat> 디렉터리)
    img_dir = Path(f"media/{chat.user_id.user_id}/{chat.chat_id}")
    if img_dir.exists():
        for p in img_dir.glob("*"):
            p.unlink(missing_ok=True)
        img_dir.rmdir()

    chat.delete()   # CASCADE 로 Message 도 삭제

    return JsonResponse({"response": 200,
                         "message": "chat deletion success",
                         "data": None})

@csrf_exempt
def chat_demo(request):
    return render(request, "api/chat_demo.html")
