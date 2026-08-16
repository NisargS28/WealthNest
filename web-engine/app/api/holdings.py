from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from app.api.auth import get_auth_token
from app.services.aggregation_service import AggregationService
from app.models.schemas import HoldingDetail

router = APIRouter()

@router.get("/holdings", response_model=List[HoldingDetail])
def get_holdings_data(
    portfolio_id: Optional[str] = Query(None),
    family_id: Optional[str] = Query(None),
    token: Optional[str] = Depends(get_auth_token)
):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    svc = AggregationService(token)
    try:
        user = svc.supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
        return svc.get_holdings(user_id, portfolio_id=portfolio_id, family_id=family_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
