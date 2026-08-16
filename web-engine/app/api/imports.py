from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import Optional
from pathlib import Path
import shutil
import os

from app.api.auth import get_auth_token
from app.services.import_service import ImportService, run_import_pipeline_background

from app.models.schemas import ImportPreview

# Directory to hold uploaded PDF files for parsing
UPLOADS_DIR = Path("uploads")

router = APIRouter()

@router.post("/import/upload", response_model=dict)
def upload_cas(
    background_tasks: BackgroundTasks,
    portfolio_id: Optional[str] = Form(None),
    password: str = Form(None),
    file: UploadFile = File(...),
    token: Optional[str] = Depends(get_auth_token),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    svc = ImportService(token)
    try:
        user = svc.supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    
    # Resolve portfolio_id to the user's default portfolio if not provided
    if not portfolio_id or portfolio_id == "default":
        try:
            ports = svc.supabase.table("portfolios").select("id").eq("owner_user_id", user_id).execute().data
            if not ports:
                raise HTTPException(status_code=400, detail="No portfolio found for the user.")
            portfolio_id = ports[0]["id"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to resolve default portfolio: {str(e)}")
    
    import_id = svc.start_import(portfolio_id, user_id, file.filename)

    upload_dir = UPLOADS_DIR / import_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(upload_dir / "cas.pdf")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Background task handles PDF parsing and inserting transactions staging data
    background_tasks.add_task(
        run_import_pipeline_background,
        import_id,
        file_path,
        password,
        portfolio_id,
        user_id,
        file.filename,
        token or ""
    )

    return {"import_id": import_id, "status": "UPLOADED"}


@router.get("/import/{import_id}/status")
def get_status(import_id: str, token: Optional[str] = Depends(get_auth_token)):
    # Query status directly from imports table
    svc = ImportService(token or "")
    try:
        import_record = svc.supabase.table("imports").select("*").eq("id", import_id).execute().data
        if not import_record:
            raise HTTPException(status_code=404, detail="Import session not found")
        return import_record[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/{import_id}/preview", response_model=ImportPreview)
def get_preview(import_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = ImportService(token or "")
    try:
        return svc.get_preview(import_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/{import_id}/confirm")
def confirm_import(import_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = ImportService(token or "")
    try:
        port_id = svc.confirm_import(import_id)
        return {"portfolio_id": port_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import/{import_id}/cancel")
def cancel_import(import_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = ImportService(token or "")
    try:
        svc.supabase.table("imports").update({"status": "CANCELLED"}).eq("id", import_id).execute()
        return {"import_id": import_id, "status": "CANCELLED"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
