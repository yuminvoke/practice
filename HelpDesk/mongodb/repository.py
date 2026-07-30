import datetime

from mongodb.client import client
from mongodb.schema import CategoryEnum, RoleEnum, ChatSession, Message, FAQ

db = client["helper"]
chat_sessions = db["chat_sessions"]
faqs = db["faqs"]


async def insert_chat_session(session_id: str, question: str):
    session = ChatSession(
        session_id=session_id,
        messages=[
            Message(role=RoleEnum.USER, content=question)
        ],
    )
    # Serialize the Pydantic model instance to dict
    await chat_sessions.insert_one(session.model_dump())

async def update_chat_message(session_id: str, category: str, role: RoleEnum, content: str):
    update = {
        "$push": {
            "messages": Message(role=role, content=content).model_dump()
        },
        "$set": {
            "updated_at": datetime.now(),
        },
    }

    if category is not None:
        update["$set"]["category"] = category

    await chat_sessions.update_one(
        {"session_id": session_id},
        update,
    )

async def find_faq_answer(category: str, keywords: list[str]) -> str | None:
    if category not in {enum.value for enum in CategoryEnum}:
        return None

    pipeline = [
        {"$match": {"category": category, "keywords": {"$in": keywords}}},
        {
            "$addFields": {
                "match_count": {
                    "$size": {
                        "$setIntersection": ["$keywords", keywords]
                    }
                }
            }
        },
        {"$sort": {"match_count": -1}},
        {"$limit": 1},
    ]

    results = await faqs.aggregate(pipeline).to_list(length=1)

    if not results:
        return None

    return results[0]["answer"]