import asyncio

from fastapi import BackgroundTasks

from app.database import db
from app.intent import (
    ShiftRequestMessageIntent,
    parse_shift_request_message_intent,
)
from app.models import InboundMessage
from app.notifier import place_phone_call, send_sms

lock = asyncio.Lock()


async def call_unclaimed(shift_id: str):
    await asyncio.sleep(600)

    shift = db.get_shift(shift_id)
    if shift and shift.get("status") != "FILLED":
        candidates = db.get_caregivers_role(shift["role_required"])
        for c in candidates:
            await place_phone_call(c["phone"], "Shift open. Call to claim.")


async def notify_caregivers(shift_id: str, tasks: BackgroundTasks) -> dict:
    shift = db.get_shift(shift_id)
    if not shift:
        return {"ERROR": "Shift not found"}

    if shift.get("status", "OPEN") != "OPEN":
        return {"WARNING": "Shift not open"}

    candidates = db.get_caregivers_role(shift["role_required"])
    if not candidates:
        return {"WARNING": "No candidates found"}

    for c in candidates:
        msg = f"New {shift['role_required']} shift open. Reply Yes or Accept to claim."
        await send_sms(c["phone"], msg)

    tasks.add_task(call_unclaimed, shift_id)
    return {"SUCCESS": f"Sent to {len(candidates)} candidates"}


async def process_reply(msg: InboundMessage) -> dict:
    caregiver = db.get_caregiver_phone(msg.phone)
    if not caregiver:
        return {"ERROR": "Unknown number"}

    intent = await parse_shift_request_message_intent(msg.message)
    if intent != ShiftRequestMessageIntent.ACCEPT:
        return {"WARNING": "Unclear message"}

    async with lock:
        matches = db.find(
            lambda x: x.get("role_required") == caregiver["role"]
            and x.get("status", "OPEN") == "OPEN"
        )

        if not matches:
            await send_sms(caregiver["phone"], "Shift already filled.")
            return {"FAILED": "No shifts available"}

        target = matches[0]
        target["status"] = "FILLED"
        target["assigned_caregiver_id"] = caregiver["id"]

        db.save_shift(target)

        await send_sms(caregiver["phone"], "Shift confirmed.")

    return {"CLAIMED. shift_id": target["id"]}
