from fastapi import APIRouter

router = APIRouter()


@router.post("/seed")
async def seed_demo():
    pass


@router.post("/clear")
async def clear_demo():
    pass