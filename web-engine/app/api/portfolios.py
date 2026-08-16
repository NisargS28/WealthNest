from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.api.auth import get_auth_token
from app.services.portfolio_service import PortfolioService
from app.services.valuation_service import ValuationService
from app.models.schemas import PortfolioDetail, TransactionView, ValuationDetail, PortfolioSummary

router = APIRouter()

@router.get("/portfolios", response_model=list[PortfolioSummary])
def get_user_portfolios(token: Optional[str] = Depends(get_auth_token)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    svc = PortfolioService(token)
    try:
        user = svc.supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
        return svc.list_user_portfolios(user_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@router.get("/portfolio/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(portfolio_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = PortfolioService(token)
    try:
        return svc.get_portfolio(portfolio_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/portfolio/{portfolio_id}/transactions", response_model=list[TransactionView])
def get_portfolio_transactions(portfolio_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = PortfolioService(token)
    return svc.get_transactions(portfolio_id)

@router.get("/portfolio/{portfolio_id}/valuation", response_model=ValuationDetail)
def get_portfolio_valuation(portfolio_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = PortfolioService(token)
    port = svc.get_portfolio(portfolio_id)
    if port.valuation:
        return port.valuation
    raise HTTPException(status_code=404, detail="Valuation not found")

@router.post("/portfolio/{portfolio_id}/refresh-nav")
def refresh_nav(portfolio_id: str, token: Optional[str] = Depends(get_auth_token)):
    svc = ValuationService(token)
    svc.refresh_valuation(portfolio_id)
    # Return the latest valuation after refresh
    port_svc = PortfolioService(token)
    port = port_svc.get_portfolio(portfolio_id)
    return port.valuation
