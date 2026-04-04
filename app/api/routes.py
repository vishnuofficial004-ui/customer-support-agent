from fastapi import APIRouter
from app.services.conversation import handle_incoming_message
from app.schemas import MessageRequest

router = APIRouter()


@router.post("/incoming_message")
async def incoming_message(request: MessageRequest):
    response = await handle_incoming_message(request.dict())
    return response