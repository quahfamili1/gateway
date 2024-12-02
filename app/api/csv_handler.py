from fastapi import APIRouter, File, UploadFile

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    # Process CSV content
    return {"message": "CSV processed successfully."}
