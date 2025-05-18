import dotenv
import re

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
    message: str
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
        max_tokens=1024,
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
    
    response = model.invoke(trimmed)
    return response.content

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
    system_prompt = (
            "You are the best assistant that translates natural language questions "
            "into SQL queries. Refer to the provided database schema. "
            "Output ONLY the SQL between ```sql``` fences."
    )
    
    messages = [
        SystemMessage(content=system_prompt),
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
