from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.chat import ChatRequest, ChatResponse
from services.chat_service import chatbot_service

router = APIRouter(prefix="/chat", tags=["Chatbot"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Main Chatbot Endpoint
    """
    # ⚠️ TEMP user_id → replace with JWT later
    user_id = 1

    return await chatbot_service.process_message(
        message=payload.message,
        db=db,
        user_id=user_id
    )
