import os
import sys
import uuid
import pytest
from decimal import Decimal

# Add web-engine path to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", ".env.local"))
load_dotenv_path = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
if not load_dotenv_path:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=dotenv_path)

from app.services.import_service import (
    ImportService,
    get_db_connection,
    resolve_scheme_direct,
    insert_nav_record_direct
)

class MockSupabaseTable:
    def __init__(self, data):
        self.data = data
        
    def select(self, *args, **kwargs):
        return self
        
    def eq(self, *args, **kwargs):
        return self
        
    def execute(self):
        class Result:
            def __init__(self, data):
                self.data = data
        return Result(self.data)

class MockSupabaseClient:
    def __init__(self, imports_data, transactions_data):
        self.imports_data = imports_data
        self.transactions_data = transactions_data
        
    def table(self, name):
        if name == "imports":
            return MockSupabaseTable(self.imports_data)
        elif name == "import_transactions":
            return MockSupabaseTable(self.transactions_data)
        elif name == "portfolios":
            return MockSupabaseTable([{"id": "a0b8f90c-e193-4dde-929d-a01889d9eb04", "name": "Test Portfolio"}])
        return MockSupabaseTable([])

def test_aditya_birla_valuation():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Scheme details
    isin = "INF209K01LF3"
    scheme_name = "Aditya Birla Sun Life Value Fund - Growth-Regular Plan"
    correct_nav = 137.94580
    units = 1412.890
    
    # 1. Insert/resolve scheme and Correct NAV
    scheme_id = resolve_scheme_direct(isin, scheme_name)
    insert_nav_record_direct(scheme_id, correct_nav, "2026-08-14")
    
    import_id = str(uuid.uuid4())
    
    # 2. Mock imports and transactions data
    imports_data = [{
        "id": import_id,
        "portfolio_id": "a0b8f90c-e193-4dde-929d-a01889d9eb04",
        "status": "PREVIEW_READY",
        "statement_start": "2017-01-01",
        "statement_end": "2026-08-15"
    }]
    transactions_data = [{
        "import_id": import_id,
        "folio_number": "1037516429",
        "scheme_name": scheme_name,
        "isin": isin,
        "transaction_date": "2021-01-20",
        "transaction_type": "PURCHASE",
        "units": units,
        "nav": 59.7249,
        "amount": float(units * 59.7249)
    }]
    
    # 3. Initialize Service and inject Mock Client
    svc = ImportService("")
    svc.supabase = MockSupabaseClient(imports_data, transactions_data)
    
    # 4. Fetch preview
    preview = svc.get_preview(import_id)
    
    # Verify results
    holding = [h for h in preview["holdings"] if h["isin"] == isin][0]
    
    # A. Aditya Birla correct NAV and valuation
    assert holding["nav"] == correct_nav
    assert holding["total_units"] == units
    assert Decimal(str(holding["current_value"])) == Decimal(str(units)) * Decimal(str(correct_nav))
    assert abs(holding["current_value"] - 194902.24) < 0.01
    
    cursor.close()
    conn.close()

def test_motilal_oswal_folios_remain_separate():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    isin = "INF247L01BV9"
    scheme_name = "Motilal Oswal Small Cap Fund - Regular Plan Growth (Non Demat)"
    correct_nav = 16.9087
    
    # 1. Resolve scheme and insert NAV
    scheme_id = resolve_scheme_direct(isin, scheme_name)
    insert_nav_record_direct(scheme_id, correct_nav, "2026-08-14")
    
    import_id = str(uuid.uuid4())
    imports_data = [{
        "id": import_id,
        "portfolio_id": "a0b8f90c-e193-4dde-929d-a01889d9eb04",
        "status": "PREVIEW_READY",
        "statement_start": "2017-01-01",
        "statement_end": "2026-08-15"
    }]
    
    transactions_data = [
        {
            "import_id": import_id,
            "folio_number": "91048658166",
            "scheme_name": scheme_name,
            "isin": isin,
            "transaction_date": "2026-08-14",
            "transaction_type": "PURCHASE",
            "units": 2267.433,
            "nav": 16.9087
        },
        {
            "import_id": import_id,
            "folio_number": "91048339283",
            "scheme_name": scheme_name,
            "isin": isin,
            "transaction_date": "2026-08-14",
            "transaction_type": "PURCHASE",
            "units": 4730.983,
            "nav": 16.9087
        }
    ]
    
    svc = ImportService("")
    svc.supabase = MockSupabaseClient(imports_data, transactions_data)
    
    preview = svc.get_preview(import_id)
    holdings = [h for h in preview["holdings"] if h["isin"] == isin]
    
    # B. Two Motilal Oswal folios remaining separate
    # C. Same scheme across multiple folios
    assert len(holdings) == 2
    
    folios = {h["folios"][0] for h in holdings}
    assert folios == {"91048658166", "91048339283"}
    
    # Verify individual valuations
    h1 = [h for h in holdings if h["folios"][0] == "91048658166"][0]
    h2 = [h for h in holdings if h["folios"][0] == "91048339283"][0]
    
    assert abs(h1["current_value"] - (2267.433 * correct_nav)) < 0.01
    assert abs(h2["current_value"] - (4730.983 * correct_nav)) < 0.01
    
    cursor.close()
    conn.close()

def test_multiple_schemes_correct_nav_mapping():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert two separate schemes and verify correct NAV resolution (no index matching/array matching)
    scheme1_name = "Union Small Cap Fund Regular Plan - Growth"
    scheme1_isin = "INF582M01BY1"
    scheme1_nav = 59.86
    
    scheme2_name = "Invesco India Midcap Fund - Regular Plan Growth (Non Demat)"
    scheme2_isin = "INF205K01BC9"
    scheme2_nav = 199.03
    
    s1_id = resolve_scheme_direct(scheme1_isin, scheme1_name)
    s2_id = resolve_scheme_direct(scheme2_isin, scheme2_name)
    
    insert_nav_record_direct(s1_id, scheme1_nav, "2026-08-14")
    insert_nav_record_direct(s2_id, scheme2_nav, "2026-08-14")
    
    import_id = str(uuid.uuid4())
    imports_data = [{
        "id": import_id,
        "portfolio_id": "a0b8f90c-e193-4dde-929d-a01889d9eb04",
        "status": "PREVIEW_READY",
        "statement_start": "2017-01-01",
        "statement_end": "2026-08-15"
    }]
    
    transactions_data = [
        {
            "import_id": import_id,
            "folio_number": "12345",
            "scheme_name": scheme1_name,
            "isin": scheme1_isin,
            "transaction_date": "2026-08-14",
            "transaction_type": "PURCHASE",
            "units": 100.0,
            "nav": 50.0
        },
        {
            "import_id": import_id,
            "folio_number": "54321",
            "scheme_name": scheme2_name,
            "isin": scheme2_isin,
            "transaction_date": "2026-08-14",
            "transaction_type": "PURCHASE",
            "units": 10.0,
            "nav": 150.0
        }
    ]
    
    svc = ImportService("")
    svc.supabase = MockSupabaseClient(imports_data, transactions_data)
    
    preview = svc.get_preview(import_id)
    
    h1 = [h for h in preview["holdings"] if h["isin"] == scheme1_isin][0]
    h2 = [h for h in preview["holdings"] if h["isin"] == scheme2_isin][0]
    
    # D. Correct NAV mapping when multiple schemes exist
    # E. No array-position-based scheme/NAV matching
    assert h1["nav"] == scheme1_nav
    assert h2["nav"] == scheme2_nav
    assert abs(h1["current_value"] - (100.0 * scheme1_nav)) < 0.01
    assert abs(h2["current_value"] - (10.0 * scheme2_nav)) < 0.01
    
    cursor.close()
    conn.close()

def test_confirm_import():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Prepare fake import
    test_user_id = "89700e28-adc4-4008-b363-3062e6e598d0"
    test_portfolio_id = "a0b8f90c-e193-4dde-929d-a01889d9eb04"
    import_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO public.imports (id, portfolio_id, uploaded_by_user_id, status, filename) VALUES (%s, %s, %s, 'PREVIEW_READY', 'test_confirm.pdf');",
        (import_id, test_portfolio_id, test_user_id)
    )
    
    # Insert some dummy transaction in import_transactions
    tx_id = str(uuid.uuid4())
    fingerprint = f"test_fp_{str(uuid.uuid4())}"
    cursor.execute("""
        INSERT INTO public.import_transactions 
        (id, import_id, folio_number, scheme_name, isin, transaction_date, transaction_type, units, nav, amount, fingerprint)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        tx_id, import_id, "999999", "Test Scheme For Confirmation", "INF999K99999", "2026-08-14", "PURCHASE", 
        10.0, 15.0, 150.0, fingerprint
    ))
    conn.commit()
    
    # 2. Call confirm_import
    svc = ImportService("")
    svc.supabase = MockSupabaseClient([], [])
    
    port_id = svc.confirm_import(import_id)
    
    assert port_id == test_portfolio_id
    
    # Verify import status in database
    cursor.execute("SELECT status FROM public.imports WHERE id = %s;", (import_id,))
    assert cursor.fetchone()[0] == "CONFIRMED"
    
    # Verify transaction in public.transactions table
    cursor.execute("SELECT id FROM public.transactions WHERE fingerprint = %s;", (fingerprint,))
    tx_inserted_id = cursor.fetchone()
    assert tx_inserted_id is not None
    
    # 3. Clean up
    cursor.execute("DELETE FROM public.transactions WHERE fingerprint = %s;", (fingerprint,))
    cursor.execute("DELETE FROM public.import_transactions WHERE id = %s;", (tx_id,))
    cursor.execute("DELETE FROM public.imports WHERE id = %s;", (import_id,))
    conn.commit()
    cursor.close()
    conn.close()
