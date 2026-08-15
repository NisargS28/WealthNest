from decimal import Decimal
from typing import Dict, Any

from app.models.holding import FolioHolding, FolioReconciliation, ReconciliationStatus

UNIT_TOLERANCE = Decimal("0.005")


def reconstruct_folio(folio_data: Dict[str, Any]) -> FolioHolding:
    """
    Deterministically reconstructs a folio's holding state from its transaction history.
    """
    opening_units = Decimal(str(folio_data.get("opening_unit_balance", "0")))
    cas_closing_raw = folio_data.get("closing_unit_balance")
    cas_closing_units = Decimal(str(cas_closing_raw)) if cas_closing_raw is not None else None

    running_balance = opening_units

    gross_purchases = Decimal("0")
    gross_redemptions = Decimal("0")
    gross_reversals = Decimal("0")
    stamp_duty = Decimal("0")

    # Sort transactions chronologically (just in case)
    transactions = sorted(folio_data.get("transactions", []), key=lambda x: x.get("date", ""))

    for tx in transactions:
        t_type = tx.get("transaction_type")
        
        # Ensure we parse units and amounts safely
        tx_units_raw = tx.get("units")
        tx_amount_raw = tx.get("amount")
        units = Decimal(str(tx_units_raw)) if tx_units_raw else Decimal("0")
        amount = Decimal(str(tx_amount_raw)) if tx_amount_raw else Decimal("0")

        if t_type in ("PURCHASE", "SWITCH_IN", "DIVIDEND_REINVESTMENT"):
            running_balance += units
            # Accumulate gross_purchases (only money in)
            if t_type in ("PURCHASE", "SWITCH_IN", "DIVIDEND_REINVESTMENT"):
                gross_purchases += abs(amount)
                
        elif t_type in ("REDEMPTION", "SWITCH_OUT"):
            running_balance -= units
            if t_type in ("REDEMPTION", "SWITCH_OUT"):
                gross_redemptions += abs(amount)
                
        elif t_type == "REVERSAL":
            # Parser already signs reversal units and amounts as negative
            running_balance += units
            gross_reversals += amount
            
        elif t_type == "STAMP_DUTY":
            stamp_duty += abs(amount)
            
        # OTHER and DIVIDEND (payout) do not affect unit balances.

    # Net Cash Flow = Gross Purchases (in) - Gross Redemptions (out) + Gross Reversals (which subtracts from purchases)
    net_cash_flow = gross_purchases - gross_redemptions + gross_reversals

    # Reconciliation
    difference = None
    status = ReconciliationStatus.FAIL
    
    if cas_closing_units is not None:
        difference = abs(running_balance - cas_closing_units)
        if difference <= UNIT_TOLERANCE:
            status = ReconciliationStatus.PASS

    reconciliation = FolioReconciliation(
        cas_closing_units=cas_closing_units,
        calculated_closing_units=running_balance,
        difference=difference,
        status=status
    )

    return FolioHolding(
        folio_number=str(folio_data.get("folio_number")),
        amc=str(folio_data.get("amc")),
        registrar=str(folio_data.get("registrar")),
        scheme_name=str(folio_data.get("scheme_name")),
        scheme_code=folio_data.get("scheme_code"),
        isin=folio_data.get("isin"),
        plan=folio_data.get("plan"),
        option=folio_data.get("option"),
        opening_units=opening_units,
        calculated_closing_units=running_balance,
        cas_closing_units=cas_closing_units,
        gross_purchases=gross_purchases,
        gross_redemptions=gross_redemptions,
        gross_reversals=gross_reversals,
        stamp_duty=stamp_duty,
        net_cash_flow=net_cash_flow,
        reconciliation=reconciliation
    )
