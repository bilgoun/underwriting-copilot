from __future__ import annotations

from typing import List

import structlog
from fastapi import APIRouter, HTTPException, status

from ..pipeline import llm
from ..schemas import ChatMessage, LoanChatRequest, LoanChatResponse

router = APIRouter(prefix="/v1/chat", tags=["chat"])
logger = structlog.get_logger(__name__)
MAX_HISTORY_MESSAGES = 20


@router.post("/loan-assistant", response_model=LoanChatResponse)
async def loan_assistant_chat(request: LoanChatRequest) -> LoanChatResponse:
    if not request.messages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversation is empty.")

    trimmed_messages = _trim_history(request.messages)
    payload = [{"role": message.role, "content": message.content} for message in trimmed_messages]

    try:
        reply, _meta = llm.generate_loan_chat_reply(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("loan_chat_failure", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Loan assistant temporarily unavailable. Please try again.",
        ) from exc

    return LoanChatResponse(reply=reply)


def _trim_history(messages: List[ChatMessage]) -> List[ChatMessage]:
    """Keep last N messages to stay within context window."""
    if len(messages) <= MAX_HISTORY_MESSAGES:
        return messages
    return messages[-MAX_HISTORY_MESSAGES:]
