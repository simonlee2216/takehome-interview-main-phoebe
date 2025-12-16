from enum import Enum

from pydantic import BaseModel


class Certification(str, Enum):
    RN = "RN"
    LPN = "LPN"
    CNA = "CNA"


class Status(str, Enum):
    OPEN = "OPEN"
    FILLED = "FILLED"


class Shift(BaseModel):
    id: str
    role_required: Certification
    status: Status = Status.OPEN  # Default to open
    assigned_caregiver_id: str | None = None

    # To keep 'organization_id' from the json
    model_config = {"extra": "allow"}


class Caregiver(BaseModel):
    id: str
    name: str
    phone: str
    role: Certification

    model_config = {"extra": "allow"}


class IncomingMessage(BaseModel):
    phone: str
    message: str
