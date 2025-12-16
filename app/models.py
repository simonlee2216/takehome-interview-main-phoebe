from pydantic import BaseModel


class InboundMessage(BaseModel):
    phone: str
    message: str
    shift_id: str
