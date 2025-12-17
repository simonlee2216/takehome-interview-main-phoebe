from fastapi import APIRouter, BackgroundTasks, FastAPI

from app import fanout_service
from app.database import load_data
from app.models import InboundMessage

load_data()

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/shifts/{shift_id}/fanout")
async def fanout(shift_id: str, tasks: BackgroundTasks):
    return await fanout_service.notify_caregivers(shift_id, tasks)


@router.post("/messages/inbound")
async def inbound(msg: InboundMessage):
    return await fanout_service.process_reply(msg)


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app
