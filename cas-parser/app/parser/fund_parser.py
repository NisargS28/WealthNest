import re
from typing import Optional, List, Tuple
from decimal import Decimal
import logging
from datetime import datetime

from app.models.folio import Folio, Registrar
from app.parser.section_detector import FolioSection

logger = logging.getLogger(__name__)

class FundParser:
    def __init__(self):
        self.folio_no_re = re.compile(r"Folio No[:\s]+([A-Z0-9/\s]+?)(?:\s+PAN:|\s+KYC:)")
        self.isin_re = re.compile(r"\b(IN[A-Z0-9]{10})\b")
        self.scheme_code_re = re.compile(r"^([A-Z0-9]+)-(.+?)\s*(?:\(Non.Demat\)|\(Demat\))")
        self.registrar_re = re.compile(r"Registrar\s*:\s*(CAMS|KFINTECH)", re.IGNORECASE)
        self.plan_re = re.compile(r"\b(Regular Plan|Direct Plan|Regular|Direct)\b", re.IGNORECASE)
        self.option_re = re.compile(r"\b(Growth|IDCW|Dividend)\b", re.IGNORECASE)
        self.opening_bal_re = re.compile(r"Opening Unit Balance:\s*([\d,\.]+)")
        self.closing_re = re.compile(r"Closing Unit Balance:\s*([\d,\.]+)\s+NAV on ([^:]+):\s+INR\s+([\d,\.]+)\s+Total Cost Value:\s*([\d,\.]+)\s+Market Value on [^:]+:\s+INR\s+([\d,\.]+)")

    def parse_decimal(self, s: str) -> Decimal:
        return Decimal(s.replace(",", "").strip())
        
    def parse_date(self, s: str) -> Optional[datetime.date]:
        try:
            return datetime.strptime(s.strip(), "%d-%b-%Y").date()
        except ValueError:
            return None

    def parse(self, section: FolioSection) -> Folio:
        """Parses the header/footer of a FolioSection and returns a Folio model."""
        lines = section.raw_lines
        
        amc = lines[0][0].strip() if lines else ""
        folio_number = ""
        registrar = Registrar.CAMS
        scheme_name = ""
        scheme_code = None
        isin = None
        plan = None
        option = None
        opening_unit_balance = Decimal("0")
        closing_unit_balance = None
        closing_nav = None
        closing_nav_date = None
        total_cost_value = None
        market_value = None
        
        for line_text, _ in lines:
            line_text = line_text.strip()
            
            if not folio_number:
                m_folio = self.folio_no_re.search(line_text)
                if m_folio:
                    folio_number = m_folio.group(1).strip()
            
            if not isin:
                m_isin = self.isin_re.search(line_text)
                if m_isin:
                    isin = m_isin.group(1).strip()
                    
            if not registrar or registrar == Registrar.CAMS:
                m_registrar = self.registrar_re.search(line_text)
                if m_registrar:
                    reg_str = m_registrar.group(1).upper()
                    if reg_str == "CAMS":
                        registrar = Registrar.CAMS
                    elif reg_str == "KFINTECH":
                        registrar = Registrar.KFINTECH
                        
            if not scheme_code:
                m_scheme = self.scheme_code_re.search(line_text)
                if m_scheme:
                    scheme_code = m_scheme.group(1).strip()
                    scheme_name = m_scheme.group(2).strip()
                    
            if not plan:
                m_plan = self.plan_re.search(line_text)
                if m_plan:
                    plan = m_plan.group(1).strip()
                    
            if not option:
                m_option = self.option_re.search(line_text)
                if m_option:
                    option = m_option.group(1).strip()
                    
            m_opening = self.opening_bal_re.search(line_text)
            if m_opening:
                opening_unit_balance = self.parse_decimal(m_opening.group(1))
                
            m_closing = self.closing_re.search(line_text)
            if m_closing:
                closing_unit_balance = self.parse_decimal(m_closing.group(1))
                closing_nav_date = self.parse_date(m_closing.group(2))
                closing_nav = self.parse_decimal(m_closing.group(3))
                total_cost_value = self.parse_decimal(m_closing.group(4))
                market_value = self.parse_decimal(m_closing.group(5))
                
        # Fallback scheme name if not matched by scheme_code_re
        if not scheme_name and isin:
            for i, (line_text, _) in enumerate(lines):
                if isin in line_text or "ISIN:" in line_text:
                    # If the line has ' - ISIN:', use the part before it as scheme name
                    if " - ISIN:" in line_text:
                        parts = line_text.split(" - ISIN:")
                        if parts:
                            scheme_name = parts[0].strip()
                            if "-" in scheme_name:
                                pot_code, pot_name = scheme_name.split("-", 1)
                                if len(pot_code) <= 10 and pot_code.isalnum():
                                    scheme_name = pot_name.strip()
                            break
                        
        if not scheme_name:
            # Another fallback: just look for the line before opening balance
            for i, (line_text, _) in enumerate(lines):
                if self.opening_bal_re.search(line_text) and i > 0:
                    prev_line = lines[i-1][0].strip()
                    if not prev_line.startswith("Nominee") and not self.folio_no_re.search(prev_line):
                        scheme_name = prev_line
                        break
                        
        return Folio(
            folio_number=folio_number or "UNKNOWN",
            amc=amc,
            registrar=registrar,
            scheme_name=scheme_name or "UNKNOWN",
            scheme_code=scheme_code,
            isin=isin,
            plan=plan,
            option=option,
            opening_unit_balance=opening_unit_balance,
            closing_unit_balance=closing_unit_balance,
            closing_nav=closing_nav,
            closing_nav_date=closing_nav_date,
            total_cost_value=total_cost_value,
            market_value=market_value,
            transactions=[],
            sip_patterns=[]
        )
