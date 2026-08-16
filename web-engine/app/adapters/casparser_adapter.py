import hashlib
from typing import Dict, Any, List
from datetime import date, datetime
from decimal import Decimal

class CasParserAdapter:
    @staticmethod
    def _parse_date(date_val: Any) -> Any:
        if not date_val:
            return None
        if isinstance(date_val, (date, datetime)):
            return date_val.isoformat()
        # Parse format e.g. "01-Jan-2021"
        try:
            return datetime.strptime(date_val.strip(), "%d-%b-%Y").date().isoformat()
        except Exception:
            return str(date_val)
    @staticmethod
    def _generate_fingerprint(folio: str, isin: str, tx_date: date, description: str, amount: Decimal, units: Decimal) -> str:
        # Create a robust, repeatable fingerprint
        raw = f"{folio}|{isin or 'NO_ISIN'}|{tx_date.isoformat()}|{description.strip()}|{amount or '0'}|{units or '0'}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
        
    @staticmethod
    def _map_transaction_type(cas_type: str) -> str:
        # casparser returns string names like "PURCHASE", "REDEMPTION", "SIP_PURCHASE" etc.
        # As per architecture rules, parser does not do SIP inference.
        # We normalize SIP_PURCHASE back to regular PURCHASE for downstream inference.
        cas_type_upper = cas_type.upper()
        if "SIP" in cas_type_upper or "PURCHASE" in cas_type_upper:
            return "PURCHASE"
        if "REDEMPTION" in cas_type.upper():
            return "REDEMPTION"
        if "SWITCH" in cas_type.upper():
            return "SWITCH"
        if "DIVIDEND" in cas_type.upper():
            return "DIVIDEND"
        if "REVERSAL" in cas_type.upper():
            return "REVERSAL"
        if "STAMP" in cas_type.upper():
            return "STAMP_DUTY"
        return "OTHER"

    @classmethod
    def transform(cls, cas_data: Any, portfolio_id: str, user_id: str, filename: str) -> Dict[str, Any]:
        """
        Transforms a casparser CASData object into dictionaries ready for Supabase inserts.
        Returns a dict containing 'import_record' and 'transactions'.
        """
        # Create the Import record
        stmt_period = cas_data.statement_period
        
        import_record = {
            "portfolio_id": portfolio_id,
            "uploaded_by_user_id": user_id,
            "source_type": "CAS_PDF",
            "filename": filename,
            "statement_start": cls._parse_date(stmt_period.from_),
            "statement_end": cls._parse_date(stmt_period.to),
            "generated_date": cls._parse_date(stmt_period.to),
            "parser_name": "casparser",
            "parser_version": "external",
            "status": "PARSING"
        }

        transactions = []
        
        # Iterate through folios and schemes
        for folio in cas_data.folios:
            folio_number = folio.folio
            
            for scheme in folio.schemes:
                scheme_name = scheme.scheme
                isin = scheme.isin
                
                for tx in scheme.transactions:
                    tx_date = tx.date
                    desc = tx.description
                    amount = Decimal(str(tx.amount)) if tx.amount is not None else None
                    units = Decimal(str(tx.units)) if tx.units is not None else None
                    nav = Decimal(str(tx.nav)) if tx.nav is not None else None
                    balance = Decimal(str(tx.balance)) if tx.balance is not None else None
                    
                    # Normalize transaction type
                    tx_type = cls._map_transaction_type(tx.type)
                    
                    fingerprint = cls._generate_fingerprint(
                        folio_number, isin, tx_date, desc, amount, units
                    )
                    
                    tx_record = {
                        "folio_number": folio_number,
                        "scheme_name": scheme_name,
                        "isin": isin,
                        "transaction_date": cls._parse_date(tx_date),
                        "transaction_type": tx_type,
                        "transaction_subtype": tx.type,
                        "description": desc,
                        "amount": float(amount) if amount else None,
                        "units": float(units) if units else None,
                        "nav": float(nav) if nav else None,
                        "unit_balance": float(balance) if balance else None,
                        "fingerprint": fingerprint,
                        "classification": "MAPPED",
                        "validation_status": "VALID"
                    }
                    transactions.append(tx_record)
        valuations = []
        for folio in cas_data.folios:
            folio_number = folio.folio
            for scheme in folio.schemes:
                if scheme.valuation:
                    valuations.append({
                        "isin": scheme.isin,
                        "scheme_name": scheme.scheme,
                        "nav": float(scheme.valuation.nav) if scheme.valuation.nav is not None else None,
                        "nav_date": cls._parse_date(scheme.valuation.date) if scheme.valuation.date else None,
                        "value": float(scheme.valuation.value) if scheme.valuation.value is not None else None
                    })

        return {
            "import_record": import_record,
            "transactions": transactions,
            "valuations": valuations
        }
