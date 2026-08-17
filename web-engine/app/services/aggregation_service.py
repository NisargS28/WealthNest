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
                SELECT transaction_type, amount, units, transaction_date, description
                FROM public.transactions
                WHERE folio_id = %s
            """, (f_id,))
            txs = cursor.fetchall()
            
            invested = Decimal(0)
            total_units = Decimal(0)
            invested_since = None
            has_sip = False
            has_lumpsum = False
            
            for tx_type, amount, units, tx_date, desc in txs:
                tx_type_upper = (tx_type or "").upper()
                desc_upper = (desc or "").upper()
                amt = Decimal(str(amount or 0))
                unt = Decimal(str(units or 0))
                
                if tx_type_upper in ['PURCHASE', 'BUY', 'LUMPSUM', 'SWITCH_IN', 'SWITCHIN']:
                    if 'SIP' in desc_upper or 'SYSTEMATIC' in desc_upper:
                        has_sip = True
                    else:
                        has_lumpsum = True
                
                if tx_type_upper in ['PURCHASE', 'BUY', 'SWITCH_IN', 'SWITCHIN', 'SIP']:
                    invested += amt
                    total_units += unt
                    # Keep track of earliest purchase date for invested_since
                    if tx_date:
                        if invested_since is None or tx_date < invested_since:
                            invested_since = tx_date
                elif tx_type_upper in ['REDEMPTION', 'SELL', 'SWITCH_OUT', 'SWITCHOUT']:
                    # Use average cost basis for redemptions
                    old_units = total_units
                    total_units -= unt
                    if total_units <= 0:
                        invested = Decimal(0)
                        total_units = Decimal(0)
                    elif old_units > 0:
                        avg_cost = invested / old_units
                        invested -= unt * avg_cost
                elif tx_type_upper in ['DIVIDEND_REINVEST', 'REINVEST']:
                    # Reinvested dividend adds units and capital
                    invested += amt
                    total_units += unt
                elif tx_type_upper == 'REVERSAL':
                    invested -= amt
                    total_units -= unt
                    if total_units <= 0:
                        invested = Decimal(0)
                        total_units = Decimal(0)
            
            # Fetch latest 2 NAVs for this asset from valuation history
            cursor.execute("""
                SELECT nav, market_value, nav_date 
                FROM public.portfolio_valuation_holdings vh
                JOIN public.portfolio_valuations v ON vh.valuation_id = v.id
                WHERE vh.asset_id = %s
                ORDER BY v.created_at DESC
                LIMIT 2
            """, (a_id,))
            val_data = cursor.fetchall()
            
            nav = Decimal(0)
            current_value = Decimal(0)
            nav_date = None
            one_day_change = None
            one_day_change_percent = None
            
            if val_data and len(val_data) > 0:
                latest_val = val_data[0]
                nav = Decimal(str(latest_val[0] or 0))
                # The market_value in valuation is for the whole asset. 
                # If there are multiple folios per asset, we calculate it:
                current_value = total_units * nav
                nav_date = latest_val[2]
                
                if len(val_data) > 1:
                    prev_val = val_data[1]
                    prev_nav = Decimal(str(prev_val[0] or 0))
                    if prev_nav > 0:
                        one_day_change_percent = ((nav - prev_nav) / prev_nav) * Decimal(100)
                        one_day_change = total_units * (nav - prev_nav)
            
            returns = Decimal(0)
            if invested > 0:
                returns = ((current_value - invested) / invested) * Decimal(100)
                
            investment_type = "Unknown"
            if has_sip and has_lumpsum:
                investment_type = "SIP & Lumpsum"
            elif has_sip:
                investment_type = "SIP"
            elif has_lumpsum or invested > 0:
                investment_type = "Lumpsum"
            
            # Fetch SIP plan for this folio (if any)
            sip_plan_id = None
            sip_day = None
            sip_amount = None
            last_sip_date = None
            next_sip_date = None
            sip_status = None
            
            cursor.execute("""
                SELECT sp.id, sp.sip_day, sp.amount, sp.next_expected_date, sp.status
                FROM public.sip_plans sp
                WHERE sp.folio_id = %s
                LIMIT 1
            """, (f_id,))
            sip_row = cursor.fetchone()
            if sip_row:
                sip_plan_id = str(sip_row[0])
                sip_day = sip_row[1]
                sip_amount = Decimal(str(sip_row[2])) if sip_row[2] else None
                next_sip_date = sip_row[3]
                sip_status = sip_row[4]
                
                # Last SIP transaction date
                cursor.execute("""
                    SELECT MAX(transaction_date)
                    FROM public.transactions
                    WHERE folio_id = %s
                      AND (description ILIKE '%%SIP%%' OR description ILIKE '%%Systematic%%')
                      AND transaction_type IN ('PURCHASE', 'BUY')
                """, (f_id,))
                last_row = cursor.fetchone()
                if last_row and last_row[0]:
                    last_sip_date = last_row[0]
                
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
                nav_date=nav_date,
                invested_since=invested_since,
                one_day_change=one_day_change,
                one_day_change_percent=one_day_change_percent,
                investment_type=investment_type,
                sip_plan_id=sip_plan_id,
                sip_day=sip_day,
                sip_amount=sip_amount,
                last_sip_date=last_sip_date,
                next_sip_date=next_sip_date,
                sip_status=sip_status
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
        portfolio_invested_since = None
        for h in holdings:
            total_invested += h.invested
            total_value += h.current_value
            
            if h.invested_since:
                if portfolio_invested_since is None or h.invested_since < portfolio_invested_since:
                    portfolio_invested_since = h.invested_since
            
        profit_loss = total_value - total_invested
        profit_percentage = Decimal(0)
        if total_invested > 0:
            profit_percentage = (profit_loss / total_invested) * Decimal(100)
            
        one_day_change = Decimal(0)
        one_day_change_percent = Decimal(0)
        last_updated_date = None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if port_ids:
            # Fetch the latest 1-day change across portfolios
            cursor.execute("""
                SELECT SUM(one_day_change), MAX(valuation_date)
                FROM (
                    SELECT portfolio_id, one_day_change, valuation_date
                    FROM (
                        SELECT portfolio_id, one_day_change, valuation_date,
                               ROW_NUMBER() OVER(PARTITION BY portfolio_id ORDER BY valuation_date DESC, created_at DESC) as rn
                        FROM public.portfolio_valuations
                        WHERE portfolio_id = ANY(%s::uuid[])
                    ) sub
                    WHERE rn = 1
                ) latest_vals
            """, (port_ids,))
            
            res = cursor.fetchone()
            if res:
                if res[0] is not None:
                    one_day_change = Decimal(str(res[0]))
                if res[1] is not None:
                    last_updated_date = res[1]
                    
            if one_day_change and total_value > 0:
                adjusted_prev_value = total_value - one_day_change
                if adjusted_prev_value > 0:
                    one_day_change_percent = (one_day_change / adjusted_prev_value) * Decimal("100.0")
                    
        # Recent transactions
        
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
            one_day_change=one_day_change if one_day_change else None,
            one_day_change_percent=one_day_change_percent if one_day_change_percent else None,
            last_updated_date=last_updated_date,
            invested_since=portfolio_invested_since,
            portfolio_count=len(port_ids),
            recent_transactions=recent_txs,
            top_holdings=top_holdings,
            asset_allocation=asset_allocation,
            pending_actions=0,
            valuation_history=valuation_history
        )
