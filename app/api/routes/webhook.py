from fastapi import APIRouter, Request, HTTPException
from app.services.conversation import handle_message

router = APIRouter()


@router.post("/incoming_message")
async def incoming_message(request: Request):
    try:
        data = await request.json()

        # Basic validation (no hardcoding assumptions beyond required keys)
        if "from" not in data or "body" not in data:
            raise HTTPException(status_code=400, detail="Invalid payload")

        response_text = await handle_message(data)

        return {
            "success": True,
            "body": response_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))