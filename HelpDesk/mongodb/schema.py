from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    ACCOUNT = "account"
    EMAIL = "email"
    NETWORK = "network"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    PRINTER = "printer"
    SECURITY = "security"
    ACCESS = "access"
    UNKNOWN = "unknown"


class RoleEnum(str, Enum):
    USER = "user"
    AGENT = "agent"
    TOOL = "tool"


class Message(BaseModel):
    role: RoleEnum
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    session_id: str
    user_id: str = None
    category: CategoryEnum
    messages: list[Message]
    ticket_id: str = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FAQ(BaseModel):
    category: str
    question: str
    answer: str
    keywords: list[str] = Field(default_factory=list)