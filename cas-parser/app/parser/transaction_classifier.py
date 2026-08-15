import re
from typing import Tuple, Optional
from app.models.transaction import TransactionType, SubType

class TransactionClassifier:
    def __init__(self):
        self.rules = [
            (re.compile(r"\*\*\*\s*Stamp Duty\s*\*\*\*", re.IGNORECASE), TransactionType.STAMP_DUTY, None),
            (re.compile(r"Reversal", re.IGNORECASE), TransactionType.REVERSAL, SubType.SIP),
            (re.compile(r"Purchase\s*-\s*SIP\s*-\s*Instalment", re.IGNORECASE), TransactionType.PURCHASE, SubType.SIP),
            (re.compile(r"Purchase\s*-\s*SIP\b", re.IGNORECASE), TransactionType.PURCHASE, SubType.SIP),
            (re.compile(r"Systematic Investment New Purchase", re.IGNORECASE), TransactionType.PURCHASE, SubType.SIP),
            (re.compile(r"Systematic Investment Existing Folio", re.IGNORECASE), TransactionType.PURCHASE, SubType.SIP),
            (re.compile(r"^Systematic Investment Purchase", re.IGNORECASE), TransactionType.PURCHASE, SubType.SIP),
            (re.compile(r"Purchase SIP Instalment No", re.IGNORECASE), TransactionType.PURCHASE, SubType.SIP),
            (re.compile(r"^Purchase\b", re.IGNORECASE), TransactionType.PURCHASE, SubType.LUMP_SUM),
            (re.compile(r"New Purchase\b", re.IGNORECASE), TransactionType.PURCHASE, SubType.LUMP_SUM),
            (re.compile(r"Purchase Distributor", re.IGNORECASE), TransactionType.PURCHASE, SubType.LUMP_SUM),
            (re.compile(r"Redemption", re.IGNORECASE), TransactionType.REDEMPTION, None),
            (re.compile(r"Switch\s*In", re.IGNORECASE), TransactionType.SWITCH_IN, None),
            (re.compile(r"Switch\s*Out", re.IGNORECASE), TransactionType.SWITCH_OUT, None),
            (re.compile(r"IDCW.*Reinvest|Dividend.*Reinvest", re.IGNORECASE), TransactionType.DIVIDEND_REINVESTMENT, None),
            (re.compile(r"IDCW|Dividend", re.IGNORECASE), TransactionType.DIVIDEND, None),
        ]

    def classify(self, description: str) -> Tuple[TransactionType, Optional[SubType]]:
        for pattern, tx_type, subtype in self.rules:
            if pattern.search(description):
                return tx_type, subtype
        
        return TransactionType.OTHER, None
