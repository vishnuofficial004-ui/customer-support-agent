from pydantic import BaseModel

class KapsoWebhookRequest(BaseModel):
    session_id: str
    customer_id: str
    message: str