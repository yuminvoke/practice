import re
from datetime import datetime

from mongodb.client import client
from mongodb.schema import CategoryEnum, RoleEnum, ChatSession, Message

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

async def update_chat_message(session_id: str, category, role: RoleEnum, content: str):
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

async def update_ticket_id(session_id: str, ticket_id: str):
    await chat_sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "ticket_id": ticket_id,
                "updated_at": datetime.now(),
            }
        },
    )

async def find_ticket_id(session_id: str) -> str | None:
    session = await chat_sessions.find_one(
        {"session_id": session_id},
        {"_id": 0 , "ticket_id": 1},
    )

    if session is None:
        return None

    return session.get("ticket_id")

async def find_faq_answer(category: str, keywords: list[str]) -> str | None:
    if category not in {enum.value for enum in CategoryEnum}:
        return None

    normalized_keywords = list({keyword.strip() for keyword in keywords if keyword.strip()})
    if not normalized_keywords:
        return None

    keyword_match_scores = []
    for keyword in normalized_keywords:
        escaped_keyword = re.escape(keyword)
        keyword_match_scores.append(
            {
                "$cond": [
                    {
                        "$or": [
                            {"$in": [keyword, {"$ifNull": ["$keywords", []]}]},
                            {
                                "$regexMatch": {
                                    "input": {"$ifNull": ["$question", ""]},
                                    "regex": escaped_keyword,
                                    "options": "i",
                                }
                            },
                            {
                                "$regexMatch": {
                                    "input": {"$ifNull": ["$answer", ""]},
                                    "regex": escaped_keyword,
                                    "options": "i",
                                }
                            },
                        ]
                    },
                    1,
                    0,
                ]
            }
        )

    pipeline = [
        {"$match": {"category": category}},
        {
            "$addFields": {
                "match_count": {"$sum": keyword_match_scores}
            }
        },
        {"$match": {"match_count": {"$gt": 0}}},
        {"$sort": {"match_count": -1}},
        {"$limit": 1},
    ]

    cursor = await faqs.aggregate(pipeline)
    results = await cursor.to_list(length=1)

    if not results:
        return None

    return results[0]["answer"]