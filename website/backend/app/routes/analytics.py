from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def dashboard_analytics():
    pass


@router.get("/products")
async def product_analytics():
    pass