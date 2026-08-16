from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.api.auth import get_auth_token
from app.services.family_service import FamilyService
from app.services.portfolio_service import PortfolioService
from app.models.schemas import FamilyMemberBase, PortfolioSummary, FamilyView, CreateFamilyMember

router = APIRouter()

@router.get("/members", response_model=list[FamilyMemberBase])
def list_members(token: Optional[str] = Depends(get_auth_token)):
    svc = FamilyService(token)
    return svc.get_members()

@router.post("/members", response_model=FamilyMemberBase)
def create_member(request: CreateFamilyMember, token: Optional[str] = Depends(get_auth_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    svc = FamilyService(token)
    try:
        user = svc.supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
        return svc.create_member(request.display_name, user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/members/{member_id}/portfolios", response_model=list[PortfolioSummary])
def list_member_portfolios(member_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = PortfolioService(token)
    return svc.list_portfolios(member_id)

@router.get("/family", response_model=FamilyView)
def get_family_aggregate(token: Optional[str] = Depends(get_auth_token)):
    svc = PortfolioService(token)
    return svc.get_family_aggregate()
