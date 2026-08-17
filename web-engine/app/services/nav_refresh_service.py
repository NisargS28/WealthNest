import os
import logging
import requests
from decimal import Decimal
from datetime import datetime, date
import psycopg2

logger = logging.getLogger(__name__)

def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)

class NAVRefreshService:
    MFAPI_BASE = "https://api.mfapi.in/mf"

    def __init__(self):
        self.session = requests.Session()
    
    def run_full_refresh(self):
        """Runs the entire nightly refresh pipeline."""
        logger.info("Starting Full NAV Refresh Pipeline...")
        self.sync_scheme_codes()
        self.refresh_all_navs()
        self.recalculate_all_portfolios()
        self.calculate_daily_changes()
        logger.info("Completed Full NAV Refresh Pipeline.")

    def sync_scheme_codes(self):
        """Downloads the MFAPI master list and maps unmapped schemes."""
        logger.info("[NAV Refresh] Syncing scheme codes...")
        try:
            # 1. Fetch unmapped schemes
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, isin, scheme_name FROM public.schemes WHERE provider_scheme_id IS NULL;")
            unmapped_schemes = cursor.fetchall()
            
            if not unmapped_schemes:
                logger.info("[NAV Refresh] No unmapped schemes found.")
                cursor.close()
                conn.close()
                return

            # 2. Download master list from MFAPI
            logger.info("[NAV Refresh] Downloading MFAPI master list...")
            response = self.session.get(self.MFAPI_BASE, timeout=30)
            response.raise_for_status()
            master_list = response.json()
            
            # Create quick lookup by ISIN and exact name (ignoring case)
            logger.info("[NAV Refresh] Building search indexes...")
            # We don't have ISIN from the /mf endpoint directly, we would need to fetch /mf/search?q=ISIN
            # But wait, does /mf return ISIN? No, MFAPI master only returns schemeCode and schemeName.
            # We'll rely on name matching or use the search endpoint for ISINs.
            
            mapped_count = 0
            
            for scheme_id, isin, scheme_name in unmapped_schemes:
                provider_code = None
                
                # Priority 1: Search by ISIN using /mf/search
                if isin:
                    try:
                        res = self.session.get(f"{self.MFAPI_BASE}/search", params={"q": isin}, timeout=10)
                        res.raise_for_status()
                        results = res.json()
                        if results and len(results) > 0:
                            provider_code = str(results[0]["schemeCode"])
                    except Exception as e:
                        logger.warning(f"Failed to search ISIN {isin}: {e}")
                
                # Priority 2: Name match from master list
                if not provider_code and scheme_name:
                    # Very simple exact match fallback
                    for m in master_list:
                        if m["schemeName"].strip().lower() == scheme_name.strip().lower():
                            provider_code = str(m["schemeCode"])
                            break
                            
                if provider_code:
                    cursor.execute("""
                        UPDATE public.schemes 
                        SET provider = 'mfapi', provider_scheme_id = %s, updated_at = NOW()
                        WHERE id = %s;
                    """, (provider_code, scheme_id))
                    mapped_count += 1
            
            conn.commit()
            logger.info(f"[NAV Refresh] Successfully mapped {mapped_count}/{len(unmapped_schemes)} schemes.")
            
        except Exception as e:
            logger.error(f"[NAV Refresh] Failed to sync scheme codes: {e}")
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            if 'conn' in locals() and conn: conn.close()

    def refresh_all_navs(self):
        """Fetches the latest NAV for all schemes with a provider_scheme_id."""
        logger.info("[NAV Refresh] Refreshing all NAVs...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Fetch schemes that have a provider code
            cursor.execute("SELECT id, provider_scheme_id FROM public.schemes WHERE provider_scheme_id IS NOT NULL;")
            mapped_schemes = cursor.fetchall()
            
            new_records = 0
            
            for scheme_id, provider_code in mapped_schemes:
                try:
                    res = self.session.get(f"{self.MFAPI_BASE}/{provider_code}/latest", timeout=10)
                    res.raise_for_status()
                    data = res.json()
                    
                    if data and data.get("data"):
                        latest = data["data"][0]
                        nav_date_str = latest["date"]
                        nav_val_str = latest["nav"]
                        
                        nav_date = datetime.strptime(nav_date_str, "%d-%m-%Y").date()
                        nav_val = Decimal(nav_val_str)
                        
                        # Check if we already have this NAV record
                        cursor.execute("""
                            SELECT id FROM public.nav_records 
                            WHERE scheme_id = %s AND nav_date = %s;
                        """, (scheme_id, nav_date))
                        
                        if not cursor.fetchone():
                            # Insert new record
                            cursor.execute("""
                                INSERT INTO public.nav_records (scheme_id, provider, provider_scheme_id, nav, nav_date)
                                VALUES (%s, 'mfapi', %s, %s, %s);
                            """, (scheme_id, provider_code, nav_val, nav_date))
                            new_records += 1
                except Exception as ex:
                    logger.warning(f"Failed to fetch NAV for scheme code {provider_code}: {ex}")
            
            conn.commit()
            logger.info(f"[NAV Refresh] Inserted {new_records} new NAV records.")
            
        except Exception as e:
            logger.error(f"[NAV Refresh] Failed to refresh NAVs: {e}")
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            if 'conn' in locals() and conn: conn.close()

    def recalculate_all_portfolios(self):
        """Recalculates valuations for all active portfolios."""
        logger.info("[NAV Refresh] Recalculating all portfolios...")
        try:
            from app.services.valuation_service import ValuationService
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM public.portfolios;")
            portfolios = cursor.fetchall()
            
            for p in portfolios:
                portfolio_id = p[0]
                try:
                    # refresh_valuation inserts a new portfolio_valuations record
                    ValuationService().refresh_valuation(portfolio_id)
                except Exception as ex:
                    logger.error(f"Failed to recalculate portfolio {portfolio_id}: {ex}")
                    
            logger.info(f"[NAV Refresh] Recalculated {len(portfolios)} portfolios.")
        except Exception as e:
            logger.error(f"[NAV Refresh] Failed to recalculate portfolios: {e}")
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            if 'conn' in locals() and conn: conn.close()

    def calculate_daily_changes(self):
        """
        Calculates the one-day true market change for every portfolio.
        Formula: one_day_change = current_value - (previous_value + cash_flows)
        """
        logger.info("[NAV Refresh] Calculating daily changes for portfolios...")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM public.portfolios;")
            portfolios = cursor.fetchall()
            
            updates = 0
            
            for p in portfolios:
                portfolio_id = p[0]
                
                # Fetch top 2 most recent valuations
                cursor.execute("""
                    SELECT id, valuation_date, total_value 
                    FROM public.portfolio_valuations 
                    WHERE portfolio_id = %s 
                    ORDER BY valuation_date DESC, created_at DESC 
                    LIMIT 2;
                """, (portfolio_id,))
                vals = cursor.fetchall()
                
                if len(vals) < 2:
                    continue # Need at least 2 valuations to calculate a change
                    
                current_id, current_date, current_value_str = vals[0]
                prev_id, prev_date, prev_value_str = vals[1]
                
                current_value = Decimal(str(current_value_str))
                prev_value = Decimal(str(prev_value_str))
                
                if prev_value == 0:
                    continue
                
                # Query net cash flows between prev_date and current_date
                # Cash flows = (PURCHASE/SIP/LUMPSUM) - (REDEMPTION)
                cursor.execute("""
                    SELECT transaction_type, amount 
                    FROM public.transactions t
                    JOIN public.folios f ON t.folio_id = f.id
                    JOIN public.assets a ON f.asset_id = a.id
                    WHERE a.portfolio_id = %s 
                      AND t.transaction_date > %s 
                      AND t.transaction_date <= %s;
                """, (portfolio_id, prev_date, current_date))
                
                txs = cursor.fetchall()
                
                net_cash_flow = Decimal("0.0")
                for tx_type, amt_str in txs:
                    if amt_str is None:
                        continue
                    amt = Decimal(str(amt_str))
                    if tx_type in ("REDEMPTION", "SWITCH_OUT", "REVERSAL"):
                        net_cash_flow -= amt
                    elif tx_type in ("PURCHASE", "SIP", "LUMPSUM", "SWITCH_IN"):
                        net_cash_flow += amt
                        
                # True one-day market change
                # The market moved the remaining amount that wasn't injected by the user
                adjusted_prev_value = prev_value + net_cash_flow
                
                one_day_change = current_value - adjusted_prev_value
                
                if adjusted_prev_value != 0:
                    one_day_change_percent = (one_day_change / adjusted_prev_value) * Decimal("100.0")
                else:
                    one_day_change_percent = Decimal("0.0")
                    
                # Update the database record using precise Decimals
                cursor.execute("""
                    UPDATE public.portfolio_valuations 
                    SET one_day_change = %s, one_day_change_percent = %s 
                    WHERE id = %s;
                """, (one_day_change, one_day_change_percent, current_id))
                
                updates += 1
                
            conn.commit()
            logger.info(f"[NAV Refresh] Successfully updated daily changes for {updates} portfolios.")
            
        except Exception as e:
            logger.error(f"[NAV Refresh] Failed to calculate daily changes: {e}")
            if 'conn' in locals() and conn: conn.rollback()
        finally:
            if 'cursor' in locals() and cursor: cursor.close()
            if 'conn' in locals() and conn: conn.close()
