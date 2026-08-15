import re
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Tuple, Optional

from app.models.transaction import Transaction, SubType
from app.parser.section_detector import FolioSection
from app.parser.transaction_classifier import TransactionClassifier
from app.models.statement import UnparsedTransaction

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self):
        self.classifier = TransactionClassifier()
        
        # Matches a date like "15-Jul-2023" at the start of the string
        self.date_re = re.compile(r"^(\d{2}-[A-Za-z]{3}-\d{4})\s+")
        
        # We need a regex for a number which might be in parenthesis: (123.45) or 123.45
        number_re = r"\(?[\d,]+\.\d+\)?"
        
        # Full transaction: date + description + amount + units + price + balance
        self.tx_full_re = re.compile(
            rf"^(\d{{2}}-[A-Za-z]{{3}}-\d{{4}})\s+"  # Date
            rf"(.+?)\s+"                       # Description (greedy, trimmed)
            rf"({number_re})\s+"              # Amount
            rf"({number_re})\s+"              # Units
            rf"({number_re})\s+"              # Price/NAV
            rf"({number_re})$"                # Unit Balance
        )

        # Stamp duty / partial rows: date + description + amount only
        self.tx_partial_re = re.compile(
            rf"^(\d{{2}}-[A-Za-z]{{3}}-\d{{4}})\s+"  # Date
            rf"(.+?)\s+"                       # Description
            rf"({number_re})$"               # Amount only
        )

        self.system_event_re = re.compile(
            r"^(\d{2}-[A-Za-z]{3}-\d{4})\s+(\*{3}.+?\*{3})"
        )
        
        # Another pattern for cases where amount might be missing but units exist
        self.tx_no_amount_re = re.compile(
            rf"^(\d{{2}}-[A-Za-z]{{3}}-\d{{4}})\s+"  # Date
            rf"(.+?)\s+"                       # Description
            rf"({number_re})\s+"              # Units
            rf"({number_re})\s+"              # Price/NAV
            rf"({number_re})$"                # Unit Balance
        )

    def parse_decimal(self, s: str) -> Decimal:
        s = s.replace(",", "").strip()
        if s.startswith("(") and s.endswith(")"):
            return Decimal("-" + s[1:-1])
        return Decimal(s)
        
    def parse_date(self, s: str) -> datetime.date:
        return datetime.strptime(s.strip(), "%d-%b-%Y").date()

    def parse_sections(self, sections: List[FolioSection], unparsed_list: List[UnparsedTransaction]) -> None:
        """Parses transactions for all sections in-place."""
        for section in sections:
            transactions = self.parse_transactions(section.raw_lines, unparsed_list)
            # We don't store them directly in the section here, we'll return them or 
            # let the orchestrator stitch it together. We'll return them instead.
            section.transactions = transactions # attach to section dynamically

    def parse_transactions(self, lines: List[Tuple[str, int]], unparsed_list: List[UnparsedTransaction]) -> List[Transaction]:
        transactions = []
        
        i = 0
        while i < len(lines):
            line_text, page_num = lines[i]
            line_text = line_text.strip()
            
            # Skip empty lines or known headers/footers
            if not line_text:
                i += 1
                continue
                
            if "Opening Unit Balance:" in line_text or "Closing Unit Balance:" in line_text:
                i += 1
                continue
                
            if "Folio No:" in line_text or "Registrar :" in line_text:
                i += 1
                continue
                
            # If it starts with a date, it's a new transaction (or system event)
            if self.date_re.match(line_text):
                # Skip false positive headers like "01-Jan-2017 To 15-Aug-2026 Date Transaction Amount..."
                if "Date Transaction" in line_text or " To " in line_text:
                    i += 1
                    continue
                    
                # Check if it's a system event
                
                # We need to collect continuation lines.
                # Find all lines until the next date or closing balance
                full_desc_line = line_text
                j = i + 1
                while j < len(lines):
                    next_line, _ = lines[j]
                    next_line = next_line.strip()
                    
                    if not next_line:
                        j += 1
                        continue
                        
                    if self.date_re.match(next_line) or "Closing Unit Balance:" in next_line or "Opening Unit Balance:" in next_line:
                        break
                        
                    if "***" in next_line and not "Stamp Duty" in next_line: # It might be a system event continuation or just random text
                        pass
                        
                    full_desc_line += " " + next_line
                    j += 1
                
                # Now try to parse the full accumulated line
                # But first, check if the full accumulated line is a system event
                m_sys_full = self.system_event_re.match(full_desc_line)
                if m_sys_full:
                    # Intentionally ignore known non-financial CAS events
                    i = j
                    continue
                    
                tx = self._parse_single_transaction(full_desc_line, page_num)
                if tx:
                    transactions.append(tx)
                else:
                    # If full accumulated failed, try just the first line
                    tx_single = self._parse_single_transaction(line_text, page_num)
                    if tx_single:
                        transactions.append(tx_single)
                    else:
                        unparsed_list.append(UnparsedTransaction(
                            page=page_num,
                            raw_text=full_desc_line[:200],
                            reason="Regex mismatch for transaction row"
                        ))
                
                i = j
            else:
                i += 1
                
        return transactions

    def _extract_sip_details(self, tx: Transaction) -> None:
        if tx.subtype == SubType.SIP:
            tx.is_sip = True
            
            # Extract installment numbers explicitly present in description
            # E.g. "Instalment 28/299", "Instalment No - 2/299"
            m = re.search(r"Instalment(?: No\s*-)?\s*(\d+)/(\d+)", tx.description, re.IGNORECASE)
            if m:
                tx.sip_installment_number = int(m.group(1))
                tx.sip_total_installments = int(m.group(2))
            else:
                # Try just installment number (e.g. "Instalment No - 1")
                m2 = re.search(r"Instalment(?: No\s*-)?\s*(\d+)", tx.description, re.IGNORECASE)
                if m2:
                    tx.sip_installment_number = int(m2.group(1))
                else:
                    # Fallback for "Systematic Investment Purchase - 32/136" where "Instalment" is omitted
                    m3 = re.search(r"-\s*(\d+)/(\d+)", tx.description)
                    if m3:
                        tx.sip_installment_number = int(m3.group(1))
                        tx.sip_total_installments = int(m3.group(2))

    def _parse_single_transaction(self, line: str, page_num: int) -> Optional[Transaction]:
        # Try full transaction
        m_full = self.tx_full_re.match(line)
        if m_full:
            date_str, desc, amount_str, units_str, price_str, bal_str = m_full.groups()
            tx_type, subtype = self.classifier.classify(desc)
            
            tx = Transaction(
                date=self.parse_date(date_str),
                transaction_type=tx_type,
                subtype=subtype,
                description=desc.strip(),
                amount=self.parse_decimal(amount_str),
                units=self.parse_decimal(units_str),
                nav=self.parse_decimal(price_str),
                unit_balance=self.parse_decimal(bal_str),
                page_number=page_num
            )
            self._extract_sip_details(tx)
            return tx
            
        # Try partial (Stamp duty)
        m_partial = self.tx_partial_re.match(line)
        if m_partial:
            date_str, desc, amount_str = m_partial.groups()
            tx_type, subtype = self.classifier.classify(desc)
            
            tx = Transaction(
                date=self.parse_date(date_str),
                transaction_type=tx_type,
                subtype=subtype,
                description=desc.strip(),
                amount=self.parse_decimal(amount_str),
                page_number=page_num
            )
            self._extract_sip_details(tx)
            return tx
            
        # Try missing amount
        m_no_amt = self.tx_no_amount_re.match(line)
        if m_no_amt:
             date_str, desc, units_str, price_str, bal_str = m_no_amt.groups()
             tx_type, subtype = self.classifier.classify(desc)
             tx = Transaction(
                date=self.parse_date(date_str),
                transaction_type=tx_type,
                subtype=subtype,
                description=desc.strip(),
                units=self.parse_decimal(units_str),
                nav=self.parse_decimal(price_str),
                unit_balance=self.parse_decimal(bal_str),
                page_number=page_num
             )
             self._extract_sip_details(tx)
             return tx
             
        return None
