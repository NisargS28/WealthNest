import logging
from typing import Optional
from decimal import Decimal
from datetime import date
import psycopg2
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)

class ValuationService:
    def __init__(self, token: Optional[str] = None):
        self.token = token

    def refresh_valuation(self, portfolio_id: str):
        logger.info(f"Refreshing valuation for portfolio: {portfolio_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Fetch all assets for this portfolio
            cursor.execute("SELECT id, name FROM public.assets WHERE portfolio_id = %s;", (portfolio_id,))
            assets = cursor.fetchall()
            
            if not assets:
                logger.info(f"No assets found for portfolio: {portfolio_id}")
                cursor.close()
                conn.close()
                return
                
            total_value = Decimal("0.0")
            total_cost = Decimal("0.0")
            valuation_date = date.today()
            
            holdings_to_insert = []
            
            for asset_id, asset_name in assets:
                # 2. Fetch all folios and transactions for this asset
                cursor.execute("""
                    SELECT f.scheme_id, t.units, t.transaction_type, t.amount
                    FROM public.folios f
                    JOIN public.transactions t ON t.folio_id = f.id
                    WHERE f.asset_id = %s;
                """, (asset_id,))
                txs = cursor.fetchall()
                
                if not txs:
                    continue
                    
                scheme_id = txs[0][0]
                total_units = Decimal("0.0")
                cost_basis = Decimal("0.0")
                
                for s_id, units_val, tx_type, amount_val in txs:
                    u = Decimal(str(units_val)) if units_val is not None else Decimal("0.0")
                    amt = Decimal(str(amount_val)) if amount_val is not None else Decimal("0.0")
                    
                    if tx_type in ("REDEMPTION", "SWITCH_OUT"):
                        total_units -= u
                        cost_basis -= amt
                    else:
                        total_units += u
                        cost_basis += amt
                
                # Fetch latest NAV from nav_records for the scheme
                cursor.execute("""
                    SELECT nav, nav_date 
                    FROM public.nav_records 
                    WHERE scheme_id = %s 
                    ORDER BY nav_date DESC LIMIT 1;
                """, (scheme_id,))
                nav_row = cursor.fetchone()
                
                latest_nav = Decimal("0.0")
                nav_date = None
                nav_status = "STALE"
                
                if nav_row:
                    latest_nav = Decimal(str(nav_row[0]))
                    nav_date = nav_row[1]
                    nav_status = "AVAILABLE"
                else:
                    # Fallback to first tx nav if none found in nav_records
                    cursor.execute("""
                        SELECT t.nav, t.transaction_date 
                        FROM public.transactions t
                        JOIN public.folios f ON t.folio_id = f.id
                        WHERE f.asset_id = %s AND t.nav IS NOT NULL
                        ORDER BY t.transaction_date DESC LIMIT 1;
                    """, (asset_id,))
                    fallback_nav_row = cursor.fetchone()
                    if fallback_nav_row:
                        latest_nav = Decimal(str(fallback_nav_row[0]))
                        nav_date = fallback_nav_row[1]
                        nav_status = "AVAILABLE"
                
                market_value = total_units * latest_nav
                total_value += market_value
                total_cost += cost_basis
                
                holdings_to_insert.append((
                    asset_id, float(total_units), float(latest_nav), nav_date, float(market_value), nav_status
                ))
            
            # 3. Insert new portfolio_valuation record
            total_profit = total_value - total_cost
            cursor.execute("""
                INSERT INTO public.portfolio_valuations (portfolio_id, valuation_date, total_value, total_cost, total_profit)
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """, (portfolio_id, valuation_date, float(total_value), float(total_cost), float(total_profit)))
            
            valuation_id = cursor.fetchone()[0]
            conn.commit()
            
            # 4. Insert valuation holdings records
            if holdings_to_insert:
                holdings_values = [
                    (valuation_id, asset_id, units, nav, nav_date, m_val, status)
                    for asset_id, units, nav, nav_date, m_val, status in holdings_to_insert
                ]
                cursor.executemany("""
                    INSERT INTO public.portfolio_valuation_holdings (valuation_id, asset_id, units, nav, nav_date, market_value, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, holdings_values)
                conn.commit()
                
            logger.info(f"Successfully calculated valuation for {portfolio_id}: Total Value = {total_value}")
            
        except Exception as e:
            logger.error(f"Failed to refresh valuation for {portfolio_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
