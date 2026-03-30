from fastapi import APIRouter, UploadFile
from app.services.review_service import review_document

router = APIRouter()

@router.post("/review")
async def review(file: UploadFile):
    result = await review_document(file)
    return result
