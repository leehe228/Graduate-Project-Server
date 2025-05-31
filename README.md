# POS-Insight: Conversational POS Data Analyzer

<img width="1595" alt="스크린샷 2025-05-31 18 51 49" src="https://github.com/user-attachments/assets/7b87b9d5-9d06-4de2-b16b-90a5e504e501" />


## 프로젝트 소개
본 프로젝트는 2025 건국대학교 컴퓨터공학부 졸업프로젝트 졸업작품으로 개발되었습니다. (2024/09 - 2025/06)

**POS-Insight**(Graduate Project Server)는 소상공인을 위해 설계된 대화형 POS 데이터 분석 및 시각화 서비스입니다.  
사용자는 웹 인터페이스를 통해 본인이 업로드한 POS(판매 시점) 매출·재고·고객 데이터를 자연어로 질의하면,  
LLM(Large Language Model)이 텍스트를 SQL 쿼리로 자동 변환하여 SQLite 데이터베이스에서 실행하고  
결과를 표나 시각적인 그래프 형태로 반환합니다.

- **목표 사용자**: 매출 관리·분석에 전문적인 지식이 없는 소상공인  
- **핵심 기능**  
  1. **자연어→SQL(Text2SQL)**  
     사용자가 입력한 한국어 질문을 정확한 SQLite 쿼리로 변환  
  2. **멀티턴 추론(Chain-of-Thought)**  
     복잡한 질문도 단계별 루프를 통해 SQL 생성, 결과 확인, 시각화 코드 작성 등을 차례대로 수행  
  3. **자동화된 그래프 생성(Python Pyplot)**  
     SQL 결과를 기반으로 LLM이 Python 코드(․pyplot)를 생성 후 서버에서 실행하여 이미지로 반환  
  4. **파일 관리 & DB 변환**  
     CSV/XLSX 파일을 업로드하면 백엔드에서 Pandas→SQLite로 자동 변환, 스키마를 저장  
  5. **API 백엔드 서버**  
     Django REST API 형태로 구현, LangChain을 활용해 프롬프트 트리밍과 LLM 호출 최적화  

---

## 데모 소개
아래는 POS-Insight 데모 페이지(간단 HTML/CSS/JS) 기반으로 제공되는 주요 기능 및 UI 구성입니다.

### 1. 파일 목록 사이드바
- **파일 업로드**: CSV/XLSX/XLS 파일을 업로드하면 서버가 자동으로 SQLite로 변환  
  - 업종 카테고리 선택(dropdown) 가능: `default`, `cafe`, `cvs`  
- **파일 리스트**: 업로드된 파일 목록 조회 → 각 파일별 상태(처리 완료/처리 중/실패) 확인 → 삭제  
- **업종별 시스템 프롬프트**: 업로드 시 선택한 업종(`file_business_category`)에 따라 LLM에게 다른 시스템 프롬프트를 전달  

<details>
<summary>파일 업로드 인터페이스 스크린샷</summary>
  
![파일 목록 & 업종 선택](./screenshots/file_upload_and_category.png)  
</details>

### 2. 채팅 목록 사이드바
- **채팅방 생성**: “새 채팅” 버튼 클릭 → 첫 사용자 질문 입력 후 채팅방 ID/제목 생성  
- **채팅 리스트**: 기존 대화 제목·ID·최종 수정 시간 표시 → 클릭 시 해당 채팅 기록 로드  
- **채팅 삭제**: 리스트에서 × 버튼으로 채팅방 및 관련 이미지·내역 삭제  

### 3. 메인 채팅 화면
- **대화 버블**  
  - 파란색(`.user`): 사용자가 입력한 질문  
  - 회색(`.internal`): LLM 내부 추론 메시지(개발자용, “INTERNAL OFF/ON” 토글)  
  - 흰색(`.assist`): 최종 사용자에게 보여지는 LLM 응답(표현, 그래프 포함)  
- **자동 스크롤 & 입력란**: 새로운 메시지 입력 시 자동 하단 스크롤, “전송” 버튼으로 서버 호출  

<details>
<summary>채팅 화면 예시</summary>
  
![채팅 화면 예시](./screenshots/chat_interface.png)  
</details>

### 4. 그래프 시각화(예시)
- 사용자가 “지난주 일별 매출 합계 그래프 보여줘” 등 요청 → LLM이  
  1. `[T2S]` 토큰과 함께 SQL 생성  
  2. SQL 실행 결과 반환  
  3. `[PLOT]` 토큰과 함께 Python matplotlib 코드 생성 → 백엔드에서 실행 → PNG로 저장  
  4. 최종 한국어 설명 + `<END>`  
- 클라이언트 UI에서 그래프 이미지를 자동으로 `<img>` 태그로 표시  

<details>
<summary>그래프 결과 예시</summary>
  
![일별 매출 그래프](./screenshots/daily_sales_plot.png)  
</details>

---

### API Specification
API 관련 설명은 [여기](https://github.com/leehe228/Graduate-Project-Server/blob/main/API_SPECIFICATION.md) 또는 본 프로젝트에 `API_SPECIFICATION.md`에서 확인할 수 있습니다.

---

## 배포 및 실행 방법

아래 단계를 따라 로컬 개발 환경에서 POS-Insight를 실행할 수 있습니다.

**1. GitHub 저장소 클론**
```bash
git clone https://github.com/leehe228/Graduate-Project-Server.git
cd Graduate-Project-Server
```
<br>

**2. Python 가상환경 설정 (권장)**
```bash
python3 -m venv venv
. venv/bin/activate      # macOS/Linux
venv\Scripts\activate    # Windows
```
<br>

**3. 필수 패키지 설치**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
<br>

**4. 환경변수 파일(.env) 준비**
프로젝트 루트에 .env 파일을 생성하고, 다음 내용을 추가하세요:
```
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
```
- <YOUR_OPENAI_API_KEY>에는 본인의 OpenAI API 키를 입력합니다.
<br>

**5. 데이터베이스 마이그레이션**
```bash
python manage.py makemigrations
python manage.py migrate
```
<br>

**6. 슈퍼유저(관리자) 생성 (선택)**
```bash
python manage.py createsuperuser
```
- 이메일, 비밀번호 입력
<br>

**개발 서버 실행**
```bash
python manage.py runserver
```
- 기본적으로 http://127.0.0.1:8000/에서 서비스가 구동됩니다.
- 브라우저에서 http://127.0.0.1:8000/demo/ 을 열어 데모 페이지를 확인하세요.
- runserver 뒤에 <IP>:<PORT> 번호 입력 시 해당 IP, PORT로 구동됩니다.
- 어드민 페이지는 http://127.0.0.1:8000/admin/ 으로 접속합니다.

---

## 주요 디렉터리 구조
```
Graduate-Project-Server/
├─ api/
│   ├─ prompts/
│   │   ├─ default.md
│   │   ├─ cafe.md
│   │   └─ cvs.md
│   ├─ templates/
│   │   └─ chat_demo.html
│   ├─ migrations/
│   ├─ views.py
│   ├─ models.py
│   ├─ utils.py
│   └─ backend.py
├─ project/                      # Django 프로젝트 설정
│   ├─ settings.py
│   ├─ urls.py
│   └─ wsgi.py
├─ requirements.txt
├─ .env                          # OpenAI API Key 등 환경변수
├─ manage.py
└─ README.md
```

- `api/prompts/*.md`
     - 업종별(기본/카페/편의점)으로 구분된 시스템 프롬프트 파일.
     - 사용자가 업로드한 파일의 file_business_category 값에 따라 적절한 프롬프트를 선택하여 LLM에 전달합니다.
- `api/utils.py`
     - `file_to_sqlite()` → CSV/Excel→SQLite 변환
     - `execute_sqlite_query()` → SQL 실행, 결과 → Pandas DataFrame
     - `run_pyplot_code()` → Python 코드 실행 후 matplotlib Figure → PNG 저장
- `api/backend.py`
     - `langchain()` → LangChain Trimmer + OpenAI API 호출 래퍼
     - `text2sql()` → “Natural Language → SQL 쿼리” 함수, 시스템 프롬프트 상수 포함
- `api/views.py`
     - 파일 관리 API: `upload_file`, `list_files`, `delete_file`
     - 채팅 API: `start_chat`, `query_chat`, `list_chats`, `get_chat_history`, `delete_chat`
     - 시스템 프롬프트 로딩: SYSTEM_PROMPTS 딕셔너리로 `default/cvs/cafe`를 키로 사용

---

## 기능 요약

| 기능 | 설명 |
|--|--|
| 회원 관리 | Django 기본 User 대신 커스텀 User 모델 사용 (회원가입/로그인 API) |
| 파일 업로드 & 변환 | CSV/XLS(X) 업로드 → api/utils.file_to_sqlite() 사용 → 데이터프레임 → SQLite (.db) 생성 → 스키마 추출 저장 |
| 업종 선택 (카테고리) | 업로드 시 선택된 category(default/cafe/cvs)에 따라 각각 다른 시스템 프롬프트를 LLM에게 전달 |
| Text2SQL (자연어→SQL) | LangChain + OpenAI LLM 기반 Text2SQL 프롬프트 → SQLite 쿼리문 생성 |
| SQL 실행 & 결과 반환 | api/utils.execute_sqlite_query()로 쿼리 실행 → Pandas DataFrame → 미리보기(헤드5) 형태로 내부 기록 |
| 그래프 생성 (Pyplot) | LLM이 생성한 [PLOT] Python 코드를 api/utils.run_pyplot_code()로 실행 후 PNG 파일 → 클라이언트에 이미지 URL 전달 |
| 멀티턴 추론(Chain-of-Thought) | 내부 메시지(.internal role)로 LLM의 추론 과정을 저장 → 다단계 로직 적용(도구 호출→결과 피드백→최종 응답) |
| UI 데모 페이지 | HTML/CSS/JavaScript 기반 데모 → 파일 목록, 채팅 목록, 채팅 화면, 내부 로그 토글 기능 포함 |
<br>

---

## 프로젝트 구조 및 아키텍처

1. **사용자(클라이언트)**
    - 브라우저에서 데모 페이지(chat_demo.html)를 통해:
      1. 로그인 → 파일 업로드 → 채팅방 생성 → 자연어 질문 입력
      2. 내부 로그 토글(INTERNAL ON/OFF) → multi-turn 추론 확인
      3. 최종 응답(텍스트 + 그래프) 획득

2. **Django API 서버**
    - 파일 관리: 업로드 → File 모델 생성 → 백그라운드 스레드에서 CSV/XLS→SQLite 변환 → file_schema 저장
    - 채팅 관리: 채팅방 생성(Chat 모델), 메시지 저장(Message 모델)
    - LangChain 호출: langchain() 함수 사용
        - SYSTEM_PROMPT 선택: SYSTEM_PROMPTS[file_business_category]
        - multi-turn 루프: [T2S] 토큰 → SQL 생성, DB 실행 → 결과 preview
        - [PLOT] 토큰 → Python 코드 실행 → PNG 저장 → 이미지 URL 반환
        - <REQUEST_INFO>, <ASK_USER>, <END> 등을 통해 흐름 제어

3. **LLM(Text2SQL + Visualization Prompt)**
    - 각각 업종별 시스템 프롬프트(/api/prompts/default.md, cafe.md, cvs.md)
    - LangChain Trimmer로 대화 맥락을 최적화 후 OpenAI API 호출
    - SQL 출력 시 sql …, Plot 출력 시 ````python …```

---

## 실행 화면 예시 (데모)
1. 로그인
2. 업종 선택 및 업로드
3. 채팅방 생성 및 질문 입력
4. SQL 생성 및 실행 결과 (내부 로그)
5. 그래프 코드 생성 및 이미지 표시

---

## 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

---
