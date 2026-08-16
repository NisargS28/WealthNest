import logging
import psycopg2
from decimal import Decimal
from typing import Optional
from app.db.supabase import get_supabase_client
from app.models.schemas import DashboardResponse, HoldingDetail, AssetAllocation, ValuationHistory
from app.services.portfolio_service import get_db_connection

logger = logging.getLogger(__name__)

class AggregationService:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.supabase = get_supabase_client(token)

    def _get_user_portfolios(self, user_id: str, portfolio_id: Optional[str] = None, family_id: Optional[str] = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT id FROM public.portfolios WHERE owner_user_id = %s"
        params = [user_id]
        
        if portfolio_id:
            query += " AND id = %s"
            params.append(portfolio_id)
            
        cursor.execute(query, tuple(params))
        port_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return port_ids

    def get_holdings(self, user_id: str, portfolio_id: Optional[str] = None, family_id: Optional[str] = None) -> list[HoldingDetail]:
        port_ids = self._get_user_portfolios(user_id, portfolio_id, family_id)
        if not port_ids:
            return []
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        holdings = []
        
        # We need to preserve folio-level distinction.
        # For each folio, we need:
        # - current_value (from latest valuation if any)
        # - invested (sum of purchases - redemptions, or whatever logic is used. Simple sum of amount for buy transactions)
        # - nav (latest nav from valuation)
        # - units (sum of units from transactions)
        # Actually, let's look at transactions for accurate invested amount.
        
        cursor.execute("""
            SELECT 
                f.id as folio_id,
                f.folio_number,
                s.scheme_name,
                s.amc_name,
                s.isin,
                a.id as asset_id
            FROM public.folios f
            JOIN public.schemes s ON f.scheme_id = s.id
            JOIN public.assets a ON f.asset_id = a.id
            WHERE a.portfolio_id = ANY(%s::uuid[])
        """, (port_ids,))
        
        folios_data = cursor.fetchall()
        
        for f_id, f_number, s_name, amc, isin, a_id in folios_data:
            # Dynamically infer category from scheme name
            name_lower = (s_name or "").lower()
            if any(k in name_lower for k in ["index", "equity", "flexi", "large", "mid", "small", "cap", "growth", "tax", "elss", "focused"]):
                cat = "Equity"
            elif any(k in name_lower for k in ["debt", "liquid", "gilt", "treasury", "arbitrage", "bond", "short term", "corporate", "money market"]):
                cat = "Debt"
            elif any(k in name_lower for k in ["hybrid", "balanced", "asset allocator", "multi asset"]):
                cat = "Hybrid"
            elif any(k in name_lower for k in ["gold", "silver", "commodity"]):
                cat = "Gold"
            else:
                cat = "Other"

            # Get transactions for this folio to calculate invested and current units
            cursor.execute("""
                SELECT transaction_type, amount, units
                FROM public.transactions
                WHERE folio_id = %s
            """, (f_id,))
            txs = cursor.fetchall()
            
            invested = Decimal(0)
            total_units = Decimal(0)
            for tx_type, amount, units in txs:
                tx_type_upper = (tx_type or "").upper()
                if tx_type_upper in ['PURCHASE', 'BUY', 'SWITCH_IN', 'SWITCHIN']:
                    invested += Decimal(str(amount or 0))
                    total_units += Decimal(str(units or 0))
                elif tx_type_upper in ['REDEMPTION', 'SELL', 'SWITCH_OUT', 'SWITCHOUT']:
                    # We subtract redemption amount from the invested principal
                    invested -= Decimal(str(amount or 0))
                    total_units -= Decimal(str(units or 0))
                elif tx_type_upper in ['DIVIDEND_REINVEST', 'REINVEST']:
                    # Reinvested dividend adds units but not external capital cash outflow
                    total_units += Decimal(str(units or 0))
                elif tx_type_upper == 'REVERSAL':
                    # Reversals cancel out purchase units and amount
                    invested -= Decimal(str(amount or 0))
                    total_units -= Decimal(str(units or 0))
            
            # Fetch latest NAV for this asset
            cursor.execute("""
                SELECT nav, market_value, nav_date 
                FROM public.portfolio_valuation_holdings vh
                JOIN public.portfolio_valuations v ON vh.valuation_id = v.id
                WHERE vh.asset_id = %s
                ORDER BY v.created_at DESC
                LIMIT 1
            """, (a_id,))
            val_data = cursor.fetchone()
            
            nav = Decimal(0)
            current_value = Decimal(0)
            nav_date = None
            
            if val_data:
                nav = Decimal(str(val_data[0] or 0))
                # The market_value in valuation is for the whole asset. 
                # If there are multiple folios per asset, we calculate it:
                current_value = total_units * nav
                nav_date = val_data[2]
            
            returns = Decimal(0)
            if invested > 0:
                returns = ((current_value - invested) / invested) * Decimal(100)
                
            holdings.append(HoldingDetail(
                id=f_id,
                scheme_name=s_name or "Unknown",
                folio_number=f_number or "Unknown",
                amc_name=amc or "Unknown",
                category=cat,
                invested=invested,
                current_value=current_value,
                returns=returns,
                nav=nav,
                units=total_units,
                nav_date=nav_date
            ))
            
        cursor.close()
        conn.close()
        
        return holdings

    def get_dashboard(self, user_id: str) -> DashboardResponse:
        port_ids = self._get_user_portfolios(user_id)
        
        total_value = Decimal(0)
        total_invested = Decimal(0)
        
        holdings = self.get_holdings(user_id)
        
        # Calculate total invested and value from holdings
        for h in holdings:
            total_invested += h.invested
            total_value += h.current_value
            
        profit_loss = total_value - total_invested
        profit_percentage = Decimal(0)
        if total_invested > 0:
            profit_percentage = (profit_loss / total_invested) * Decimal(100)
            
        # Recent transactions
        conn = get_db_connection()
        cursor = conn.cursor()
        
        recent_txs = []
        if port_ids:
            cursor.execute("""
                SELECT t.id, t.transaction_date, t.transaction_type, t.transaction_subtype, t.description, t.amount, t.units, t.nav, t.unit_balance
                FROM public.transactions t
                JOIN public.folios f ON t.folio_id = f.id
                JOIN public.assets a ON f.asset_id = a.id
                WHERE a.portfolio_id = ANY(%s::uuid[])
                ORDER BY t.transaction_date DESC
                LIMIT 5
            """, (port_ids,))
            
            for id_val, tx_date, tx_type, subtype, description, amount, units, nav, unit_balance in cursor.fetchall():
                from app.models.schemas import TransactionView
                recent_txs.append(TransactionView(
                    id=id_val,
                    date=tx_date,
                    transaction_type=tx_type,
                    subtype=subtype,
                    description=description,
                    amount=Decimal(str(amount)) if amount is not None else None,
                    units=Decimal(str(units)) if units is not None else None,
                    nav=Decimal(str(nav)) if nav is not None else None,
                    unit_balance=Decimal(str(unit_balance)) if unit_balance is not None else None,
                    is_sip=False
                ))
                
        cursor.close()
        conn.close()
        
        # Top holdings
        top_holdings = sorted(holdings, key=lambda x: x.current_value, reverse=True)[:5]
        
        # Asset allocation (simple category breakdown)
        alloc_map = {}
        for h in holdings:
            cat = h.category or "Other"
            if cat not in alloc_map:
                alloc_map[cat] = Decimal(0)
            alloc_map[cat] += h.current_value
            
        # Hardcoded colors for now
        colors = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))", "hsl(var(--chart-5))"]
        asset_allocation = []
        for i, (cat, val) in enumerate(alloc_map.items()):
            if val > 0:
                asset_allocation.append(AssetAllocation(
                    name=cat,
                    value=val,
                    color=colors[i % len(colors)]
                ))
                
        # Empty valuation history for now
        valuation_history = []
        
        return DashboardResponse(
            total_value=total_value,
            total_invested=total_invested,
            profit_loss=profit_loss,
            profit_percentage=profit_percentage,
            portfolio_count=len(port_ids),
            recent_transactions=recent_txs,
            top_holdings=top_holdings,
            asset_allocation=asset_allocation,
            pending_actions=0,
            valuation_history=valuation_history
        )
