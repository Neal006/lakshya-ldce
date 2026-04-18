from fastapi import APIRouter

router = APIRouter()


@router.post("/email/inbound")
async def inbound_email():
    pass