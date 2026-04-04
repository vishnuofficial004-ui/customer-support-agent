from fastapi import APIRouter
from app.schemas.session_schema import KapsoWebhookRequest
from app.services.conversation import handle_incoming_message

router = APIRouter()

@router.post("/webhook")
async def kapso_webhook(payload: KapsoWebhookRequest):
    session_id = payload.session_id
    customer_id = payload.customer_id
    message = payload.message

    response = await handle_incoming_message(session_id, customer_id, message)
    return {"success": True, "response": response}