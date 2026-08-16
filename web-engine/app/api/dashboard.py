from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.api.auth import get_auth_token
from app.services.aggregation_service import AggregationService
from app.models.schemas import DashboardResponse

router = APIRouter()

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard_data(token: Optional[str] = Depends(get_auth_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    svc = AggregationService(token)
    try:
        user = svc.supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
        return svc.get_dashboard(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
