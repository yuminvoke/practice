from fastapi import FastAPI
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from api.schema import ChatRequest, ChatResponse
from helper.agent import root_agent
from mongodb.client import client
from mongodb.schema import ChatSession, Message

APP_NAME = "IT Help Desk"

app = FastAPI(title="HelpDesk API")

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

db = client["helper"]
chat_sessions= db["chat_sessions"]


def classify_category(question: str) -> str:
    rules = {
        "account": ["비밀번호", "계정", "로그인", "SSO", "권한"],
        "email": ["메일", "이메일", "수신", "발송", "첨부"],
        "network": ["와이파이", "Wi-Fi", "VPN", "인터넷", "네트워크"],
        "hardware": ["노트북", "모니터", "키보드", "마우스", "전원"],
        "software": ["프로그램", "소프트웨어", "설치", "오류", "마이크"],
        "printer": ["프린터", "인쇄", "출력", "용지"],
        "security": ["피싱", "백신", "악성코드", "바이러스", "보안"],
        "access": ["공유 폴더", "접근", "파일 서버"],
    }

    for category, keywords in rules.items():
        if any(keyword.lower() in question.lower() for keyword in keywords):
            return category

    return "unknown"


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    category = classify_category(request.question)

    session = ChatSession(
        session_id=request.session_id,
        category=category,
        messages=[
            Message(role="user", content=request.question)
        ],
    )

    await chat_sessions.insert_one(session.model_dump())

    return ChatResponse()