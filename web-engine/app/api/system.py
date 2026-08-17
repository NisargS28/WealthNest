from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import Optional
from app.api.auth import get_auth_token
from app.services.nav_refresh_service import NAVRefreshService

router = APIRouter()

@router.post("/trigger-nav-refresh")
def trigger_nav_refresh(
    background_tasks: BackgroundTasks,
    token: Optional[str] = Depends(get_auth_token)
):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    """
    Manually triggers the daily NAV refresh and portfolio recalculation.
    Runs as a background task.
    """
    service = NAVRefreshService()
    background_tasks.add_task(service.run_full_refresh)
    
    return {
        "status": "success",
        "message": "NAV refresh pipeline has been triggered in the background."
    }
