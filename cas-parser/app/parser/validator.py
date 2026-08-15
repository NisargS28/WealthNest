from decimal import Decimal
import logging
from typing import List

from app.models.folio import Folio
from app.models.transaction import TransactionType, TransactionValidation, NavValidation
from app.models.statement import ValidationWarning

logger = logging.getLogger(__name__)

class Validator:
    def __init__(self):
        self.unit_tolerance = Decimal("0.005") # 3 decimal places tolerance
        self.nav_monetary_tolerance = Decimal("0.5")  # Due to 3 decimal place truncation on units, the calculated monetary amount can drift.
        
    def validate(self, folio: Folio) -> List[ValidationWarning]:
        """Validates transactions in a folio and returns a list of warnings."""
        warnings = []
        
        # Sort transactions chronologically
        transactions = sorted(folio.transactions, key=lambda x: (x.date, x.page_number))
        folio.transactions = transactions
        
        current_balance = folio.opening_unit_balance
        
        for tx in transactions:
            tx.validation = TransactionValidation(unit_balance_match=True)
            
            # 1. NAV Validation
            if tx.amount and tx.units and tx.nav and tx.units != 0:
                # Due to CAS unit truncation (3 decimals), Amount/Units diverges from true NAV.
                # Instead, verify if the reported amount matches Units * Reported NAV within monetary tolerance.
                expected_amount = abs(tx.units * tx.nav)
                actual_amount = abs(tx.amount)
                diff = abs(expected_amount - actual_amount)
                
                match = diff <= self.nav_monetary_tolerance
                tx.validation.nav_validation = NavValidation(
                    calculated_nav=round(actual_amount / abs(tx.units), 4),
                    reported_nav=tx.nav,
                    difference=round(diff, 4), # Repurposing difference as monetary difference in model
                    match=match
                )
                
                if not match:
                    warnings.append(ValidationWarning(
                        folio=folio.folio_number,
                        transaction_date=tx.date,
                        message=f"NAV/Amount mismatch: Expected amount {expected_amount:.2f}, got {actual_amount:.2f}, diff={diff:.4f} (NAV={tx.nav})"
                    ))
            
            # 2. Unit Balance Validation
            if tx.unit_balance is not None:
                expected_balance = current_balance
                
                if tx.units is not None:
                    if tx.transaction_type in (TransactionType.PURCHASE, TransactionType.SWITCH_IN, TransactionType.DIVIDEND_REINVESTMENT, TransactionType.REVERSAL):
                        # Reversals extract negative units naturally, so += applies a reduction correctly
                        expected_balance += tx.units
                    elif tx.transaction_type in (TransactionType.REDEMPTION, TransactionType.SWITCH_OUT):
                        # Redemptions extract positive units generally, so -= reduces balance
                        expected_balance -= tx.units
                
                # Check difference
                diff = abs(expected_balance - tx.unit_balance)
                if diff <= self.unit_tolerance:
                    tx.validation.unit_balance_match = True
                    tx.validation.unit_balance_difference = diff
                    current_balance = tx.unit_balance  # Trust the CAS moving forward
                else:
                    # Only warn if we actually expected a unit change or if the balance changed unexpectedly
                    if tx.transaction_type != TransactionType.STAMP_DUTY and tx.transaction_type != TransactionType.OTHER:
                        tx.validation.unit_balance_match = False
                        tx.validation.unit_balance_difference = diff
                        
                        warnings.append(ValidationWarning(
                            folio=folio.folio_number,
                            transaction_date=tx.date,
                            message=f"Unit balance mismatch: expected {expected_balance:.3f}, got {tx.unit_balance:.3f}, diff={diff:.3f}"
                        ))
                    
                    # For next calculations, we use the reported balance to prevent cascading errors
                    current_balance = tx.unit_balance
            
        return warnings
