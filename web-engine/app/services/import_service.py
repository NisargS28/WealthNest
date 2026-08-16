import os
import logging
import psycopg2
from typing import Optional, Dict, Any, List
from decimal import Decimal
from app.db.supabase import get_supabase_client
from app.pipeline.orchestrator import run_pipeline

logger = logging.getLogger(__name__)

def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)

def resolve_scheme_direct(isin: Optional[str], scheme_name: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    scheme_id = None
    if isin:
        cursor.execute("SELECT id FROM public.schemes WHERE isin = %s;", (isin,))
        row = cursor.fetchone()
        if row:
            scheme_id = row[0]
            
    if not scheme_id:
        cursor.execute("SELECT id FROM public.schemes WHERE scheme_name = %s;", (scheme_name,))
        row = cursor.fetchone()
        if row:
            scheme_id = row[0]
            
    if not scheme_id:
        cursor.execute(
            "INSERT INTO public.schemes (isin, scheme_name) VALUES (%s, %s) RETURNING id;",
            (isin, scheme_name)
        )
        scheme_id = cursor.fetchone()[0]
        conn.commit()
        
    cursor.close()
    conn.close()
    return scheme_id

def insert_nav_record_direct(scheme_id: str, nav: float, nav_date: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM public.nav_records WHERE scheme_id = %s AND nav_date = %s;",
        (scheme_id, nav_date)
    )
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO public.nav_records (scheme_id, nav, nav_date) VALUES (%s, %s, %s);",
            (scheme_id, nav, nav_date)
        )
        conn.commit()
        
    cursor.close()
    conn.close()

def get_closing_nav_direct(isin: Optional[str], scheme_name: str) -> Optional[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    row = None
    if isin:
        cursor.execute("""
            SELECT n.nav, n.nav_date 
            FROM public.nav_records n
            JOIN public.schemes s ON n.scheme_id = s.id
            WHERE s.isin = %s
            ORDER BY n.nav_date DESC LIMIT 1;
        """, (isin,))
        row = cursor.fetchone()
        
    if not row:
        cursor.execute("""
            SELECT n.nav, n.nav_date 
            FROM public.nav_records n
            JOIN public.schemes s ON n.scheme_id = s.id
            WHERE s.scheme_name = %s
            ORDER BY n.nav_date DESC LIMIT 1;
        """, (scheme_name,))
        row = cursor.fetchone()
        
    cursor.close()
    conn.close()
    
    if row:
        return {"nav": row[0], "nav_date": row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1])}
    return None

def run_import_pipeline_background(
    import_id: str,
    pdf_path: str,
    password: Optional[str],
    portfolio_id: str,
    user_id: str,
    filename: str,
    token: str
):
    """
    Runs casparser in the background, then saves the result to Supabase using the provided user token.
    """
    logger.info(f"[BG] Pipeline starting for import {import_id}")
    supabase = get_supabase_client(token)
    
    try:
        # Update status to PARSING
        supabase.table("imports").update({"status": "PARSING"}).eq("id", import_id).execute()
        
        # Run pipeline
        adapted_data = run_pipeline(pdf_path, password, portfolio_id, user_id, filename)
        
        import_record = adapted_data["import_record"]
        transactions = adapted_data["transactions"]
        valuations = adapted_data.get("valuations", [])
        
        # Resolve schemes and save closing NAVs in background
        for val in valuations:
            try:
                scheme_id = resolve_scheme_direct(val["isin"], val["scheme_name"])
                if val["nav"] is not None and val["nav_date"]:
                    insert_nav_record_direct(scheme_id, val["nav"], val["nav_date"])
            except Exception as ex:
                logger.error(f"[BG] Failed to insert NAV record: {str(ex)}")
        
        # Update import record with statement period and status
        supabase.table("imports").update({
            "statement_start": import_record["statement_start"],
            "statement_end": import_record["statement_end"],
            "generated_date": import_record["generated_date"],
            "status": "PREVIEW_READY"
        }).eq("id", import_id).execute()
        
        # Insert import_transactions
        # Add import_id to all transactions
        for tx in transactions:
            tx["import_id"] = import_id
            
        if transactions:
            # Batch insert import_transactions
            supabase.table("import_transactions").insert(transactions).execute()
            
        logger.info(f"[BG] Import {import_id} → PREVIEW_READY")

    except Exception as e:
        logger.error(f"[BG] Pipeline failed for {import_id}: {str(e)}")
        try:
            supabase.table("imports").update({"status": "FAILED", "error_message": str(e)}).eq("id", import_id).execute()
        except Exception:
            pass
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass


class ImportService:
    def __init__(self, token: str):
        self.token = token
        self.supabase = get_supabase_client(token)

    def start_import(self, portfolio_id: str, user_id: str, original_filename: str) -> str:
        """
        Creates an Import record in Supabase.
        Returns the import_id.
        """
        response = self.supabase.table("imports").insert({
            "portfolio_id": portfolio_id,
            "uploaded_by_user_id": user_id,
            "source_type": "CAS_PDF",
            "filename": original_filename,
            "status": "UPLOADED"
        }).execute()
        
        if not response.data:
            raise ValueError("Failed to create import record")
            
        return response.data[0]["id"]

    def confirm_import(self, import_id: str) -> str:
        """
        Moves new transactions from import_transactions to transactions.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Fetch import record
        cursor.execute("SELECT status, portfolio_id FROM public.imports WHERE id = %s;", (import_id,))
        import_row = cursor.fetchone()
        if not import_row or import_row[0] != "PREVIEW_READY":
            cursor.close()
            conn.close()
            raise ValueError("Import is not ready for confirmation")
            
        portfolio_id = import_row[1]
        
        # 2. Fetch all import_transactions for this import
        cursor.execute("""
            SELECT folio_number, scheme_name, isin, transaction_date, transaction_type, transaction_subtype, description, amount, units, nav, unit_balance, fingerprint
            FROM public.import_transactions
            WHERE import_id = %s;
        """, (import_id,))
        import_txs = cursor.fetchall()
        
        if import_txs:
            # Fetch existing transaction fingerprints
            cursor.execute("SELECT fingerprint FROM public.transactions;")
            existing_fps = {row[0] for row in cursor.fetchall()}
            
            # Fetch existing schemes
            cursor.execute("SELECT id, isin, scheme_name FROM public.schemes;")
            existing_schemes = cursor.fetchall()
            scheme_map = {row[1]: row[0] for row in existing_schemes if row[1]}
            scheme_name_map = {row[2]: row[0] for row in existing_schemes}
            
            # Fetch existing folios for this portfolio
            cursor.execute("""
                SELECT f.id, f.folio_number, f.scheme_id 
                FROM public.folios f
                JOIN public.assets a ON f.asset_id = a.id
                WHERE a.portfolio_id = %s;
            """, (portfolio_id,))
            existing_folios_for_portfolio = cursor.fetchall()
            folio_map = {f"{row[1]}_{row[2]}": row[0] for row in existing_folios_for_portfolio}
            existing_folio_numbers = {row[1] for row in existing_folios_for_portfolio}
            
            new_tx_values = []
            
            for row in import_txs:
                (folio_number, scheme_name, isin, transaction_date, transaction_type, transaction_subtype, 
                 description, amount, units, nav, unit_balance, fingerprint) = row
                 
                # DUPLICATE CAS IMPORT RULE: Skip transactions if the folio already exists in this portfolio
                if folio_number in existing_folio_numbers:
                    continue
                 
                if fingerprint not in existing_fps:
                    # 1. Resolve Scheme
                    scheme_id = None
                    if isin and isin in scheme_map:
                        scheme_id = scheme_map[isin]
                    elif scheme_name in scheme_name_map:
                        scheme_id = scheme_name_map[scheme_name]
                    else:
                        cursor.execute(
                            "INSERT INTO public.schemes (isin, scheme_name) VALUES (%s, %s) RETURNING id;",
                            (isin, scheme_name)
                        )
                        scheme_id = cursor.fetchone()[0]
                        conn.commit()
                        if isin:
                            scheme_map[isin] = scheme_id
                        scheme_name_map[scheme_name] = scheme_id
                        
                    # 2. Resolve Asset and Folio
                    folio_key = f"{folio_number}_{scheme_id}"
                    folio_id = None
                    if folio_key in folio_map:
                        folio_id = folio_map[folio_key]
                    else:
                        # Create Asset
                        cursor.execute("""
                            INSERT INTO public.assets (portfolio_id, asset_type, name)
                            VALUES (%s, 'MUTUAL_FUND', %s) RETURNING id;
                        """, (portfolio_id, scheme_name))
                        asset_id = cursor.fetchone()[0]
                        conn.commit()
                        
                        # Create Folio
                        cursor.execute("""
                            INSERT INTO public.folios (asset_id, scheme_id, folio_number)
                            VALUES (%s, %s, %s) RETURNING id;
                        """, (asset_id, scheme_id, folio_number))
                        folio_id = cursor.fetchone()[0]
                        conn.commit()
                        folio_map[folio_key] = folio_id
                        
                    # 3. Add to values list
                    new_tx_values.append((
                        folio_id, scheme_id, import_id, transaction_date, transaction_type, transaction_subtype,
                        description, amount, units, nav, unit_balance, 'CAS_PDF', fingerprint
                    ))
                    
            if new_tx_values:
                cursor.executemany("""
                    INSERT INTO public.transactions (
                        folio_id, scheme_id, import_id, transaction_date, transaction_type, transaction_subtype,
                        description, amount, units, nav, unit_balance, source_type, fingerprint
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, new_tx_values)
                conn.commit()
                
            # Update import record status
            cursor.execute(
                "UPDATE public.imports SET status = 'CONFIRMED', confirmed_at = NOW() WHERE id = %s;",
                (import_id,)
            )
            conn.commit()
            
            # Recalculate portfolio valuation immediately on confirm
            try:
                from app.services.valuation_service import ValuationService
                ValuationService().refresh_valuation(portfolio_id)
            except Exception as val_ex:
                logger.error(f"Failed to refresh valuation on confirm: {str(val_ex)}")
            
        cursor.close()
        conn.close()
        return portfolio_id

    def get_preview(self, import_id: str) -> dict:
        import_record = self.supabase.table("imports").select("*").eq("id", import_id).execute().data
        if not import_record:
            raise ValueError("Import not found")
        
        # Get portfolio owner name
        portfolio_id = import_record[0]["portfolio_id"]
        port = self.supabase.table("portfolios").select("*").eq("id", portfolio_id).execute().data
        owner_name = port[0]["name"] if port else "Unknown Owner"
        
        # Fetch import transactions
        txs = self.supabase.table("import_transactions").select("*").eq("import_id", import_id).execute().data
        
        # Staging values
        funds = len(set(tx["scheme_name"] for tx in txs))
        folios = len(set(tx["folio_number"] for tx in txs))
        
        # Fetch existing folios for duplicate risk
        assets = self.supabase.table("assets").select("id").eq("portfolio_id", portfolio_id).execute().data
        asset_ids = [a["id"] for a in assets]
        existing_folios = set()
        if asset_ids:
            # We can use .in_() or fetch all and filter. Supabase python .in_ expects a list of strings/ints
            # It's safer to fetch all folios and filter if we have a lot, or just use .in_
            folios_res = self.supabase.table("folios").select("folio_number").in_("asset_id", asset_ids).execute().data
            existing_folios = {f["folio_number"] for f in folios_res}
        
        # Count types
        purchases = sum(1 for tx in txs if tx["transaction_type"] == "PURCHASE")
        redemptions = sum(1 for tx in txs if tx["transaction_type"] == "REDEMPTION")
        switches = sum(1 for tx in txs if "SWITCH" in tx["transaction_type"])
        reversals = sum(1 for tx in txs if tx["transaction_type"] == "REVERSAL")
        stamp_duty = sum(1 for tx in txs if tx["transaction_type"] == "STAMP_DUTY")
        other = len(txs) - (purchases + redemptions + switches + reversals + stamp_duty)
        
        # Build holdings preview (group by (isin or scheme_name, folio_number) using Decimals)
        holdings_map = {}
        for tx in txs:
            s_name = tx["scheme_name"]
            isin = tx["isin"]
            folio_num = tx["folio_number"]
            key = (isin or s_name, folio_num)
            
            if key not in holdings_map:
                holdings_map[key] = {
                    "scheme_name": s_name,
                    "amc": "",
                    "isin": isin,
                    "folios": [folio_num],
                    "total_units": Decimal("0.0"),
                    "nav": None,
                    "nav_date": None,
                    "current_value": Decimal("0.0"),
                    "nav_status": "AVAILABLE",
                    "mapping_method": "ISIN" if isin else "NAME"
                }
            
            units = Decimal(str(tx["units"])) if tx["units"] is not None else Decimal("0.0")
            if tx["transaction_type"] == "REDEMPTION":
                holdings_map[key]["total_units"] -= units
            else:
                holdings_map[key]["total_units"] += units
                
        # Resolve correct closing NAVs for each (scheme, folio) holding row
        holdings = []
        for key, h in holdings_map.items():
            # Query db for closing NAV of this scheme
            nav_info = get_closing_nav_direct(h["isin"], h["scheme_name"])
            if nav_info:
                h["nav"] = Decimal(str(nav_info["nav"]))
                h["nav_date"] = nav_info["nav_date"]
                h["current_value"] = h["total_units"] * h["nav"]
            else:
                # Fallback to NAV of first transaction if no closing NAV was saved
                # Find first tx for this scheme/folio that has a nav
                fallback_nav = None
                tx_date = None
                for tx in txs:
                    if (tx["isin"] == h["isin"] or tx["scheme_name"] == h["scheme_name"]) and tx["folio_number"] == h["folios"][0]:
                        if tx.get("nav") is not None:
                            fallback_nav = Decimal(str(tx["nav"]))
                            tx_date = tx["transaction_date"]
                            break
                if fallback_nav is not None:
                    h["nav"] = fallback_nav
                    h["nav_date"] = tx_date
                    h["current_value"] = h["total_units"] * h["nav"]
                else:
                    h["nav_status"] = "NAV_UNAVAILABLE"
                    h["current_value"] = Decimal("0.0")
            
            # Format Decimal to float/str for json serialization
            is_new = not any(f in existing_folios for f in h["folios"])
            holdings.append({
                "scheme_name": h["scheme_name"],
                "amc": h["amc"],
                "isin": h["isin"],
                "folios": h["folios"],
                "total_units": float(h["total_units"]),
                "nav": float(h["nav"]) if h["nav"] is not None else None,
                "nav_date": h["nav_date"],
                "current_value": float(h["current_value"]),
                "nav_status": h["nav_status"],
                "mapping_method": h["mapping_method"],
                "is_new_investment": is_new
            })
            
        total_value = sum(h["current_value"] for h in holdings)
        
        new_folios_count = sum(1 for h in holdings if h["is_new_investment"])
        existing_folios_count = len(holdings) - new_folios_count
        
        return {
            "import_id": import_id,
            "portfolio_owner": owner_name,
            "status": import_record[0]["status"],
            "duplicate_risk": False,
            "duplicate_message": None,
            "summary": {
                "funds": funds,
                "folios": folios,
                "new_folios": new_folios_count,
                "existing_folios": existing_folios_count,
                "transactions": len(txs),
                "total_current_value": total_value,
                "nav_data_date": import_record[0].get("statement_end"),
                "statement_period_start": import_record[0].get("statement_start"),
                "statement_period_end": import_record[0].get("statement_end")
            },
            "transaction_breakdown": {
                "purchases": purchases,
                "redemptions": redemptions,
                "switches": switches,
                "reversals": reversals,
                "stamp_duty": stamp_duty,
                "other": other
            },
            "holdings": holdings,
            "validation": {
                "parser_warnings": 0,
                "reconciliation_warnings": 0,
                "nav_errors": 0,
                "unmatched_schemes": 0,
                "stale_nav_schemes": 0,
                "warnings": []
            }
        }
