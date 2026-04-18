from fastapi import APIRouter

router = APIRouter()


@router.get("/stream")
async def complaint_stream():
    pass