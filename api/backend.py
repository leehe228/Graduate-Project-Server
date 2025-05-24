import dotenv
import re
from typing import Generator, Union

from langchain_core.messages.utils import trim_messages
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)
from langchain_openai.chat_models import ChatOpenAI

# Load environment variables from .env file
dotenv.load_dotenv()

def langchain(
    model: ChatOpenAI,
    system_prompt: str | None,
    prev_messages: list[dict[str, str]] | None,
    message: str,
    max_tokens: int = 4096,
    streaming: bool = False
) -> str:
    """
    Args:
      system_prompt: 모델에게 주는 초기 지시문 (system 역할)
      prev_messages: 과거 대화 기록, [{"role":"user"|"assistant","content": "..."}]
      message:       최종 사용자의 질문 내용

    Returns:
      모델이 생성한 응답 문자열
    """
    
    trimmer = trim_messages(
        max_tokens=max_tokens,
        strategy="last",
        token_counter=model,
        include_system=True,
        allow_partial=True,
        start_on="human"
    )
    
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
        
    if prev_messages:
        for item in prev_messages:
            if item["role"] == "user":
                messages.append(HumanMessage(content=item["content"]))
            elif item["role"] == "assistant":
                messages.append(AIMessage(content=item["content"]))
                
    trimmed = trimmer.invoke(messages) if messages else []
    trimmed.append(HumanMessage(content=message))
    
    if streaming:
        def gen():
            for chunk in model.stream(trimmed):
                delta = chunk.content
                if delta:
                    yield delta
        return gen()
    else:
        return model.invoke(trimmed).content


POS_TEXT2SQL_PROMPT = r"""You are “POS-SQL-Gen”, an expert assistant that turns natural-language
questions about point-of-sale (POS) data into SQLite-compatible SQL.

Rules
- ALWAYS output only a fenced code-block that starts with ```sql and ends
  with ``` – no prose, no comments outside the fence.
- Use only table / column names that exist in the schema provided by the user
  (never invent names; ask for clarification if unsure).
- Use ISO-8601 dates; rely on SQLite helpers (DATE, strftime) when filtering
  by month or day.
- When a filter is implied (e.g., “지난달”, “최근 3개월”), compute the correct
  date range directly in SQL.
- SQL query must be valid and executable in SQLite.
- If the question is ambigous or too complex, ask for clarification.

Few-shot Examples  
Schema excerpt for all examples  
- Table orders      (order_id INTEGER, order_date DATE, customer_id INTEGER, total REAL)
- Table order_items (order_id INTEGER, product_id INTEGER, quantity INTEGER, line_total REAL)
- Table products    (product_id INTEGER, product_name TEXT, category TEXT, current_stock INTEGER)
- Table customers   (customer_id INTEGER, gender TEXT, age_group TEXT)

### 1. 지난달 가장 많이 팔린 메뉴
NL → “지난달 가장 많이 팔린 메뉴는?”
```sql
SELECT p.product_name,
       SUM(oi.quantity) AS total_qty
FROM   order_items AS oi
JOIN   orders      AS o  USING(order_id)
JOIN   products    AS p  USING(product_id)
WHERE  o.order_date >= DATE('now','start of month','-1 month')
  AND  o.order_date <  DATE('now','start of month')
GROUP  BY p.product_id
ORDER  BY total_qty DESC
LIMIT  1;
```

### 2. 최근 3개월 매출 추이
NL → “최근 3개월 매출 추이 보여줘”
```sql
SELECT strftime('%Y-%m', o.order_date) AS month,
       SUM(o.total)                    AS monthly_sales
FROM   orders AS o
WHERE  o.order_date >= DATE('now','start of month','-3 months')
GROUP  BY month
ORDER  BY month;
```

### 3. 20대 여성 고객 인기 상품
NL → “20대 여성 고객이 가장 많이 산 상품은?”
```sql
SELECT p.product_name,
       SUM(oi.quantity) AS total_qty
FROM   order_items AS oi
JOIN   orders      AS o  USING(order_id)
JOIN   customers   AS c  ON c.customer_id = o.customer_id
JOIN   products    AS p  USING(product_id)
WHERE  c.gender = 'F'
  AND  c.age_group = '20s'
GROUP  BY p.product_id
ORDER  BY total_qty DESC
LIMIT  1;
```

### 4. 재고 부족 상품
NL → “재고 부족 또는 폐기율 높은 상품은?”
```sql
SELECT product_name,
       current_stock
FROM   products
WHERE  current_stock < 10;
```

### 5. 신제품 출시 전-후 매출 비교
NL → “신제품 출시 후 기존 메뉴 매출은?”
```sql
-- assume launch_date = '2025-04-01'
SELECT CASE WHEN o.order_date < '2025-04-01' THEN 'Before' ELSE 'After' END AS period,
       SUM(o.total) AS sales
FROM   orders AS o
WHERE  o.order_date BETWEEN DATE('2025-01-01') AND DATE('now')
GROUP  BY period;
```"""

def text2sql(
    model: ChatOpenAI,
    query: str,
    db_schema: str
) -> str:
    """
    간단한 Text-to-SQL 변환 함수.
    
    Args:
        query:       자연어 질문 문자열
        db_schema:   대상 데이터베이스의 스키마 (텍스트)
    
    Returns:
        SQL 쿼리문 (```sql ...``` 사이의 내용만)
    """
    # system_prompt = (
    #         "You are the best assistant that translates natural language questions "
    #         "into SQL queries. Refer to the provided database schema. "
    #         "Output ONLY the SQL between ```sql``` fences."
    # )
    
    messages = [
        SystemMessage(content=POS_TEXT2SQL_PROMPT),
        HumanMessage(content=(
            f"Database schema:\n{db_schema}\n\n"
            f"Convert the following question into SQL and wrap it in ```sql``` fences:\n"
            f"NL Question: {query}"
        ))
    ]
    
    response = model.invoke(messages)
    content = response.content
    
    match = re.search(r"```sql\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return content.strip()

def make_title(
    model: ChatOpenAI,
    message: str,
    max_length: int = 32
) -> str:
    """
    Generate a title for the chat based on the message content.
    Args:
        message:     The message content to generate a title from.
        max_length:  The maximum length of the title.
    Returns:
        A string representing the generated title, truncated to max_length if necessary.
    """
    
    system_prompt = (
        "You are a title generator. "
        "Generate a concise title for the following message content."
        f"Max length of title is {max_length} characters."
        "Make a title in Korean."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            "Generate a title for the following message:\n"
            f"Message: {message}\n"
        ))
    ]
    
    response = model.invoke(messages)
    content = response.content.strip()
    if len(content) > max_length:
        content = content[:max_length]
        
    return content
