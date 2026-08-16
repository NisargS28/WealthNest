import logging
import psycopg2
import os
from decimal import Decimal
from typing import Optional
from app.db.supabase import get_supabase_client
from app.models.schemas import (
    PortfolioSummary, PortfolioDetail, StoredHolding, StoredFolio, 
    ValuationDetail, TransactionView, FamilyView, FamilyAggregate
)
from app.services.family_service import FamilyService

logger = logging.getLogger(__name__)

def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)

class PortfolioService:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.supabase = get_supabase_client(token)

    def list_user_portfolios(self, user_id: str) -> list[PortfolioSummary]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get portfolios
        cursor.execute("SELECT id, name, created_at FROM public.portfolios WHERE owner_user_id = %s;", (user_id,))
        ports = cursor.fetchall()
        
        result = []
        for port_id, name, created_at in ports:
            # Get asset IDs
            cursor.execute("SELECT id FROM public.assets WHERE portfolio_id = %s;", (port_id,))
            asset_ids = [row[0] for row in cursor.fetchall()]
            
            folio_count = 0
            tx_count = 0
            
            if asset_ids:
                # Get folio count
                cursor.execute("SELECT id FROM public.folios WHERE asset_id = ANY(%s::uuid[]);", (asset_ids,))
                folio_ids = [row[0] for row in cursor.fetchall()]
                folio_count = len(folio_ids)
                
                if folio_ids:
                    # Get transaction count
                    cursor.execute("SELECT COUNT(*) FROM public.transactions WHERE folio_id = ANY(%s::uuid[]);", (folio_ids,))
                    tx_count = cursor.fetchone()[0]
                    
            # Get latest valuation
            cursor.execute("""
                SELECT total_value, valuation_date 
                FROM public.portfolio_valuations 
                WHERE portfolio_id = %s 
                ORDER BY created_at DESC LIMIT 1;
            """, (port_id,))
            latest_val = cursor.fetchone()
            
            if not latest_val:
                try:
                    from app.services.valuation_service import ValuationService
                    ValuationService(self.token).refresh_valuation(port_id)
                    cursor.execute("""
                        SELECT total_value, valuation_date 
                        FROM public.portfolio_valuations 
                        WHERE portfolio_id = %s 
                        ORDER BY created_at DESC LIMIT 1;
                    """, (port_id,))
                    latest_val = cursor.fetchone()
                except Exception as val_ex:
                    logger.error(f"Failed to auto-refresh valuation for portfolio {port_id}: {str(val_ex)}")
                    
            val_value = Decimal(str(latest_val[0])) if latest_val else None
            val_date = latest_val[1] if latest_val else None
            
            result.append(PortfolioSummary(
                id=port_id,
                member_id="",
                display_name=name,
                created_at=created_at,
                total_current_value=val_value,
                last_valuation_date=val_date,
                folio_count=folio_count,
                transaction_count=tx_count
            ))
            
        cursor.close()
        conn.close()
        return result

    def list_portfolios(self, member_id: str) -> list[PortfolioSummary]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get portfolios for the given member_id
        cursor.execute("SELECT id, name, created_at FROM public.portfolios WHERE member_id = %s;", (member_id,))
        ports = cursor.fetchall()
        
        result = []
        for port_id, name, created_at in ports:
            # Get asset IDs
            cursor.execute("SELECT id FROM public.assets WHERE portfolio_id = %s;", (port_id,))
            asset_ids = [row[0] for row in cursor.fetchall()]
            
            folio_count = 0
            tx_count = 0
            
            if asset_ids:
                # Get folio count
                cursor.execute("SELECT id FROM public.folios WHERE asset_id = ANY(%s::uuid[]);", (asset_ids,))
                folio_ids = [row[0] for row in cursor.fetchall()]
                folio_count = len(folio_ids)
                
                if folio_ids:
                    # Get transaction count
                    cursor.execute("SELECT COUNT(*) FROM public.transactions WHERE folio_id = ANY(%s::uuid[]);", (folio_ids,))
                    tx_count = cursor.fetchone()[0]
                    
            # Get latest valuation
            cursor.execute("""
                SELECT total_value, valuation_date 
                FROM public.portfolio_valuations 
                WHERE portfolio_id = %s 
                ORDER BY created_at DESC LIMIT 1;
            """, (port_id,))
            latest_val = cursor.fetchone()
            
            val_value = Decimal(str(latest_val[0])) if latest_val else None
            val_date = latest_val[1] if latest_val else None
            
            result.append(PortfolioSummary(
                id=port_id,
                member_id=member_id,
                display_name=name,
                created_at=created_at,
                total_current_value=val_value,
                last_valuation_date=val_date,
                folio_count=folio_count,
                transaction_count=tx_count
            ))
            
        cursor.close()
        conn.close()
        return result

    def get_portfolio(self, portfolio_id: str) -> PortfolioDetail:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get Portfolio
        cursor.execute("SELECT id, name, owner_user_id FROM public.portfolios WHERE id = %s;", (portfolio_id,))
        p = cursor.fetchone()
        if not p:
            cursor.close()
            conn.close()
            raise ValueError("Portfolio not found")
            
        owner_user_id = p[2]
        port_name = p[1]
        
        # 2. Get assets
        cursor.execute("SELECT id, name, asset_type FROM public.assets WHERE portfolio_id = %s;", (portfolio_id,))
        assets = cursor.fetchall()
        asset_ids = [a[0] for a in assets]
        
        folios = []
        if asset_ids:
            # Get folios and schemes
            cursor.execute("""
                SELECT f.id, f.folio_number, s.amc_name, s.scheme_name, s.isin
                FROM public.folios f
                LEFT JOIN public.schemes s ON f.scheme_id = s.id
                WHERE f.asset_id = ANY(%s::uuid[]);
            """, (asset_ids,))
            folios_db = cursor.fetchall()
            
            for f_id, folio_number, amc_name, scheme_name, isin in folios_db:
                cursor.execute("SELECT COUNT(*) FROM public.transactions WHERE folio_id = %s;", (f_id,))
                tx_count = cursor.fetchone()[0]
                
                folios.append(StoredFolio(
                    folio_number=folio_number,
                    amc=amc_name or "",
                    scheme_name=scheme_name or "",
                    isin=isin,
                    opening_units=Decimal("0"),
                    cas_closing_units=None,
                    transaction_count=tx_count
                ))
                
        # 3. Get latest valuation
        cursor.execute("""
            SELECT id, created_at, total_value 
            FROM public.portfolio_valuations 
            WHERE portfolio_id = %s 
            ORDER BY created_at DESC LIMIT 1;
        """, (portfolio_id,))
        latest_val = cursor.fetchone()
        
        if not latest_val:
            try:
                from app.services.valuation_service import ValuationService
                ValuationService(self.token).refresh_valuation(portfolio_id)
                cursor.execute("""
                    SELECT id, created_at, total_value 
                    FROM public.portfolio_valuations 
                    WHERE portfolio_id = %s 
                    ORDER BY created_at DESC LIMIT 1;
                """, (portfolio_id,))
                latest_val = cursor.fetchone()
            except Exception as val_ex:
                logger.error(f"Failed to auto-refresh valuation for portfolio {portfolio_id}: {str(val_ex)}")
                
        val_detail = None
        if latest_val:
            val_id, val_created_at, val_total_value = latest_val
            
            # Fetch valuation holdings
            cursor.execute("""
                SELECT vh.asset_id, vh.units, vh.nav, vh.nav_date, vh.market_value, vh.status, a.name
                FROM public.portfolio_valuation_holdings vh
                JOIN public.assets a ON vh.asset_id = a.id
                WHERE vh.valuation_id = %s;
            """, (val_id,))
            val_holdings_db = cursor.fetchall()
            
            val_holdings = []
            for asset_id, units, nav, nav_date, market_value, status, asset_name in val_holdings_db:
                # Fetch folio numbers for this asset
                cursor.execute("SELECT folio_number FROM public.folios WHERE asset_id = %s;", (asset_id,))
                f_list = [row[0] for row in cursor.fetchall()]
                
                val_holdings.append(StoredHolding(
                    scheme_name=asset_name or "",
                    amc="",
                    isin=None,
                    total_units=Decimal(str(units)),
                    current_value=Decimal(str(market_value)),
                    nav=Decimal(str(nav)) if nav is not None else None,
                    nav_date=nav_date,
                    nav_status=status or "STALE",
                    folios=f_list
                ))
                
            val_detail = ValuationDetail(
                portfolio_id=portfolio_id,
                generated_at=val_created_at,
                total_current_value=Decimal(str(val_total_value)),
                holdings=val_holdings
            )
            
        cursor.close()
        conn.close()
        
        from app.services.aggregation_service import AggregationService
        agg_svc = AggregationService(self.token)
        rich_holdings = agg_svc.get_holdings(user_id=owner_user_id, portfolio_id=portfolio_id)
        
        return PortfolioDetail(
            id=portfolio_id,
            member_id=owner_user_id or "",
            display_name=port_name,
            holdings=rich_holdings,
            folios=folios,
            valuation=val_detail
        )

    def get_transactions(self, portfolio_id: str) -> list[TransactionView]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Fetch assets
        cursor.execute("SELECT id FROM public.assets WHERE portfolio_id = %s;", (portfolio_id,))
        asset_ids = [row[0] for row in cursor.fetchall()]
        if not asset_ids:
            cursor.close()
            conn.close()
            return []
            
        # 2. Fetch folios
        cursor.execute("SELECT id FROM public.folios WHERE asset_id = ANY(%s::uuid[]);", (asset_ids,))
        folio_ids = [row[0] for row in cursor.fetchall()]
        if not folio_ids:
            cursor.close()
            conn.close()
            return []
            
        # 3. Fetch transactions
        cursor.execute("""
            SELECT t.id, t.transaction_date, t.transaction_type, t.transaction_subtype, t.description, t.amount, t.units, t.nav, t.unit_balance
            FROM public.transactions t
            WHERE t.folio_id = ANY(%s::uuid[])
            ORDER BY t.transaction_date DESC;
        """, (folio_ids,))
        txs = cursor.fetchall()
        
        result = []
        for id_val, tx_date, tx_type, subtype, description, amount, units, nav, unit_balance in txs:
            result.append(TransactionView(
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
        return result

    def get_family_aggregate(self) -> FamilyView:
        members_service = FamilyService(self.token)
        members = members_service.get_members()
        
        total_val = Decimal(0)
        member_summaries = []
        for member in members:
            ports = self.list_portfolios(member.id)
            for p in ports:
                member_summaries.append(p)
                if p.total_current_value:
                    total_val += p.total_current_value
                    
        return FamilyView(
            members=members,
            aggregate=FamilyAggregate(
                total_value=total_val,
                member_summaries=member_summaries
            )
        )

    def delete_portfolio(self, portfolio_id: str, authenticated_user_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Verify ownership
            cursor.execute("SELECT owner_user_id FROM public.portfolios WHERE id = %s;", (portfolio_id,))
            port = cursor.fetchone()
            if not port:
                raise ValueError("Portfolio not found")
                
            if port[0] != authenticated_user_id:
                raise ValueError("Unauthorized to delete this portfolio")
                
            # 2. Get assets
            cursor.execute("SELECT id FROM public.assets WHERE portfolio_id = %s;", (portfolio_id,))
            asset_ids = [row[0] for row in cursor.fetchall()]
            
            # 3. Get folios
            folio_ids = []
            if asset_ids:
                cursor.execute("SELECT id FROM public.folios WHERE asset_id = ANY(%s::uuid[]);", (asset_ids,))
                folio_ids = [row[0] for row in cursor.fetchall()]
                
            # 4. Get imports
            cursor.execute("SELECT id FROM public.imports WHERE portfolio_id = %s;", (portfolio_id,))
            import_ids = [row[0] for row in cursor.fetchall()]
            
            # 5. Get valuations
            cursor.execute("SELECT id FROM public.portfolio_valuations WHERE portfolio_id = %s;", (portfolio_id,))
            valuation_ids = [row[0] for row in cursor.fetchall()]

            # Execute Deletions (respecting foreign keys)
            
            # A. Delete import_transactions
            if import_ids:
                cursor.execute("DELETE FROM public.import_transactions WHERE import_id = ANY(%s::uuid[]);", (import_ids,))
                
            # B. Delete imports
            cursor.execute("DELETE FROM public.imports WHERE portfolio_id = %s;", (portfolio_id,))
            
            # C. Delete portfolio_valuation_holdings
            if valuation_ids:
                cursor.execute("DELETE FROM public.portfolio_valuation_holdings WHERE valuation_id = ANY(%s::uuid[]);", (valuation_ids,))
                
            # D. Delete portfolio_valuations
            cursor.execute("DELETE FROM public.portfolio_valuations WHERE portfolio_id = %s;", (portfolio_id,))
            
            # E. Delete SIP Occurrences and SIP Plans
            if folio_ids:
                cursor.execute("SELECT id FROM public.sip_plans WHERE folio_id = ANY(%s::uuid[]);", (folio_ids,))
                sip_plan_ids = [row[0] for row in cursor.fetchall()]
                if sip_plan_ids:
                    cursor.execute("DELETE FROM public.sip_occurrences WHERE sip_plan_id = ANY(%s::uuid[]);", (sip_plan_ids,))
                    cursor.execute("DELETE FROM public.sip_plans WHERE folio_id = ANY(%s::uuid[]);", (folio_ids,))
            
            # F. Delete transactions
            if folio_ids:
                cursor.execute("DELETE FROM public.transactions WHERE folio_id = ANY(%s::uuid[]);", (folio_ids,))
                
            # G. Delete folios
            if asset_ids:
                cursor.execute("DELETE FROM public.folios WHERE asset_id = ANY(%s::uuid[]);", (asset_ids,))
                
            # H. Delete assets
            cursor.execute("DELETE FROM public.assets WHERE portfolio_id = %s;", (portfolio_id,))
            
            # I. Delete the portfolio itself
            cursor.execute("DELETE FROM public.portfolios WHERE id = %s;", (portfolio_id,))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
