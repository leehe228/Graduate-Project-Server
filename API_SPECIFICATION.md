# API Specification

## 서버 상태 코드

- **200**: 성공 (Success)
- **400**: 값 누락 (Bad Request)
- **401**: 인증 실패 (Unauthorized)
- **404**: 찾을 수 없음 (Not Found)
- **405**: 올바르지 않은 요청 방법 (Method Not Allowed)
- **409**: 충돌 발생 (Conflict)
- **500**: 내부 오류 (Internal Server Error)

---

## 서버 상태 체크

### [GET] 서버 Healthy Check (구현 완료)

**Request Address**
```
{{server_address}}/api/health
```

**Response**
성공
```json
{
  "response": 200,
  "message": "server connection success",
  "data": null
}
```

실패
– 200 응답을 제외한 모든 경우 (응답 없음, 비정상 응답 등)

⸻

## 회원 관리

### [POST] 회원 가입 (구현 완료)

**Request Address**
```
{{server_address}}/api/auth/register
```

**Body (Raw-JSON)**
```
{
  "user_id": "tester",
  "user_email": "test@email.com",
  "user_password": "password1234",
  "user_name": "tester",
  "user_category": 0
}
```

**Response**
성공
```
{
  "response": 200,
  "message": "register success",
  "data": null
}
```

실패 (값 누락 혹은 빈 값)
```
{
  "response": 400,
  "message": "missing required fields",
  "data": null
}
```

실패 (아이디 중복)
```
{
  "response": 409,
  "message": "user id already exists",
  "data": null
}
```

실패 (이메일 중복)
```
{
  "response": 409,
  "message": "email already exists",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [POST] 로그인 (구현 완료)

**Request Address**
```
{{server_address}}/api/auth/login
```

**Body (Raw-JSON)**
```
{
  "user_id": "tester",
  "user_password": "password1234"
}
```

**Response**

성공
```
{
  "response": 200,
  "message": "login success",
  "data": null
}
```

실패 (값 누락 혹은 빈 값)
```
{
  "response": 400,
  "message": "missing required fields",
  "data": null
}
```

실패 (로그인 실패)
```
{
  "response": 401,
  "message": "invalid user id or password",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [GET] 유저 정보 조회 (구현 완료)

**Request Address**
```
{{server_address}}/api/auth/user?user_id=<USER_ID>
```
- parameters
    - `user_id`: 정보 조회할 유저 아이디

**Response**

성공
```
{
  "response": 200,
  "message": "request success",
  "data": {
    "user_id": "tester",
    "user_email": "test@email.com",
    "user_name": "Hoeun Lee",
    "user_category": 0,
    "created_at": "2025-05-18 13:00:00"
  }
}
```

실패 (값 누락 혹은 빈 값)
```
{
  "response": 400,
  "message": "missing required fields",
  "data": null
}
```

실패 (사용자 아이디 찾을 수 없음)
```
{
  "response": 404,
  "message": "user id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

## 파일 관리

### [POST] 파일 업로드 (구현 완료)

**Request Address**
```
{{server_address}}/api/files/upload
```

**Body (form-data)**

| Key	| Type	| Value e.g.	| 주석 |
|--|--|--|--|
| `file` | File | 실제 파일 | 업로드할 파일 |
| `user_id` | Text | "tester" | 파일 소유자 User ID |
| `category`| Text | "cvs" | 파일 업종 카테고리 [“default”, “cvs”, “cafe”] |
<br>

**Response**

성공
```
{
  "response": 200,
  "message": "file upload success",
  "data": null
}
```

실패 (값 누락 혹은 빈 값)
```
{
  "response": 400,
  "message": "missing required fields",
  "data": null
}
```

실패 (파일 카테고리 값이 잘못됨)
```
{
  "response": 400,
  "message": "invalid file category",
  "data": null
}
```

실패 (파일이 없거나 잘못됨)
```
{
  "response": 400,
  "message": "file is invalid",
  "data": null
}
```

실패 (User ID 없음)
```
{
  "response": 404,
  "message": "user id is not found",
  "data": null
}
```

실패 (파일 용량이 제한 크기 이상임)
```
{
  "response": 413,
  "message": "file is too large",
  "data": null
}
```

실패 (지원하지 않는 확장자)
```
{
  "response": 415,
  "message": "unsupported file type",
  "data": null
}
```
- .csv, .xls, .xlsx만 지원함

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [GET] 파일 목록 조회 (구현 완료)

**Request Address**
```
{{server_address}}/api/files/list?user_id=<USER_ID>
```
- parameters
    -	`user_id`: 정보 조회할 유저 아이디

**Response**

성공
```
{
  "response": 200,
  "message": "request success",
  "data": [
    {
      "file_id": 8,
      "file_name": "pos_test.csv",
      "file_size_kb": 0,
      "file_size_b": 594,
      "file_type": "csv",
      "file_path": "static/files/tester/6f9ea913-a14e-4143-a17f-06d220c5d5d3.csv",
      "file_processed": true,
      "file_error": "",
      "created_at": "2025-05-24 18:03:23",
      "file_business_category": "default"
    },
    {
      "file_id": 9,
      "file_name": "dummy_cafe.csv",
      "file_size_kb": 0,
      "file_size_b": 701,
      "file_type": "csv",
      "file_path": "static/files/tester/dc5fe9c1-8113-476f-8451-553af1625824.csv",
      "file_processed": true,
      "file_error": "",
      "created_at": "2025-05-31 09:01:31",
      "file_business_category": "cvs"
    }
  ]
}
```

실패 (사용자 아이디 존재하지 않음)
```
{
  "response": 404,
  "message": "user id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [DELETE] 파일 삭제 (구현 완료)

**Request Address**
```
{{server_address}}/api/files/delete?file_id=<FILE_ID>
```
-	parameters
    -	`file_id`: 삭제할 파일의 ID

**Response**

성공
```
{
  "response": 200,
  "message": "file deletion success",
  "data": null
}
```

실패 (파일 아이디 존재하지 않음)
```
{
  "response": 404,
  "message": "file id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

## 채팅

### [POST] 채팅 시작 - 채팅방 생성

**Request Address**
```
{{server_address}}/api/chat/start
```

**Body (Raw-JSON)**
```
{
  "user_id": "tester",
  "message_text": "hello?",
  "file_id": 0
}
```
- 채팅방 생성은 첫 메시지와 함께 전송

**Response**

성공
```
{
  "response": 200,
  "message": "chat creation success",
  "data": {
    "chat_id": 20,
    "chat_title": "일별 매출 합계 막대 그래프",
    "response": "The bar chart displays the total daily sales over the specified period. Each bar represents the sum of sales for a particular day, allowing you to easily compare sales performance across different dates.",
    "image_url": "/media/tester/20/e359e063-8500-4c90-9815-29e708e87bcc.png"
  }
}
```
- 생성된 채팅 아이디, 응답, 제목 반환
- 이미지 포함된 경우 이미지 URL 함께 반환

실패 (사용자 아이디 찾을 수 없음)
```
{
  "response": 404,
  "message": "user id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [POST] 메시지 전송 및 응답 수신

**Request Address**
```
{{server_address}}/api/chat/query
```

**Body (Raw-JSON)**
```
{
  "chat_id": 1,
  "message_text": "hello?"
}
```

**Response**

성공
```
{
  "response": 200,
  "message": "query request success",
  "data": {
    "response": "전체 매출 합계는 83.9입니다.",
    "image_url": null
  }
}
```
- 이미지 포함된 경우 이미지 URL 함께 반환

실패 (채팅 아이디 찾을 수 없음)
```
{
  "response": 404,
  "message": "chat id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [GET] 채팅방 목록 조회

**Request Address**
```
{{server_address}}/api/chat/list?user_id=<USER_ID>
```
- parameters
    - `user_id`: 채팅방 목록 조회할 유저 아이디

**Response**

성공
```
{
  "response": 200,
  "message": "request success",
  "data": {
    "chats": [
      {
        "chat_id": 20,
        "chat_title": "일별 매출 합계 막대 그래프",
        "created_at": "2025/05/18 20:33:19",
        "updated_at": "2025/05/18 20:33:20"
      },
      {
        "chat_id": 19,
        "chat_title": "Top-Selling Bakery Product?",
        "created_at": "2025/05/18 20:32:32",
        "updated_at": "2025/05/18 20:32:32"
      }
    ]
  }
}
```

실패 (사용자 아이디 존재하지 않음)
```
{
  "response": 404,
  "message": "user id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [GET] 채팅 기록 조회 - 채팅방 내 메시지 조회

**Request Address**
```
{{server_address}}/api/chat/history?chat_id=<CHAT_ID>
```
- parameters
    - `chat_id`: 채팅방 내 메시지 목록 조회할 채팅 아이디

**Response**

성공
```
{
  "response": 200,
  "message": "request success",
  "data": {
    "messages": [
      {
        "message_id": 59,
        "message_text": "전체 일별 매출 합계를 막대 그래프로 보여줘",
        "message_role": "user",
        "message_image_url": null,
        "created_at": "2025/05/18 20:33:20"
      },
      {
        "message_id": 62,
        "message_text": "The bar chart displays the total daily sales over the specified period. Each bar represents the sum of sales for a particular day, allowing you to easily compare sales performance across different dates.",
        "message_role": "assistant",
        "message_image_url": "/media/tester/20/e359e063-8500-4c90-9815-29e708e87bcc.png",
        "created_at": "2025/05/18 20:33:24"
      },
      {
        "message_id": 63,
        "message_text": "모두 합치면 얼마야?",
        "message_role": "user",
        "message_image_url": null,
        "created_at": "2025/05/18 20:33:50"
      },
      {
        "message_id": 65,
        "message_text": "전체 매출 합계는 83.9입니다.",
        "message_role": "assistant",
        "message_image_url": null,
        "created_at": "2025/05/18 20:33:52"
      }
    ]
  }
}
```
- message_role의 경우 사용자는 "user", AI 응답은 "assistant"

실패 (채팅 아이디 존재하지 않음)
```
{
  "response": 404,
  "message": "chat id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```

⸻

### [DELETE] 채팅방 삭제

**Request Address**
```
{{server_address}}/api/chat/delete?chat_id=<CHAT_ID>
```
- parameters
    - chat_id: 삭제할 채팅의 ID

**Response**

성공
```
{
  "response": 200,
  "message": "chat deletion success",
  "data": null
}
```

실패 (채팅 아이디 존재하지 않음)
```
{
  "response": 404,
  "message": "chat id is not found",
  "data": null
}
```

실패 (내부 오류)
```
{
  "response": 500,
  "message": "internal server error",
  "data": null
}
```
