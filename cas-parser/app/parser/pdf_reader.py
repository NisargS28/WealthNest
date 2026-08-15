import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import pdfplumber
import fitz  # PyMuPDF
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PageContent:
    page_number: int
    raw_text: str  # From PyMuPDF (joined lines)
    raw_lines: List[str]  # From PyMuPDF (split by newline)
    table_rows: List[List[Optional[str]]]  # From pdfplumber


class PdfReader:
    def __init__(self, pdf_path: str, password: Optional[str] = None):
        self.pdf_path = pdf_path
        self.password = password
        self.metadata: Dict[str, Any] = {}
        self.statement_metadata = {
            "period_start": None,
            "period_end": None,
            "generated_date": None
        }
        self.portfolio_summary = []
        self.pages: List[PageContent] = []

    def process(self) -> List[PageContent]:
        """Process the PDF using PyMuPDF and pdfplumber, return page contents."""
        logger.info(f"Opening PDF: {self.pdf_path}")
        
        # 1. Open with PyMuPDF
        try:
            doc = fitz.open(self.pdf_path)
            if doc.needs_pass:
                if not self.password:
                    raise ValueError("PDF is encrypted but no password provided.")
                if not doc.authenticate(self.password):
                    raise ValueError("Invalid PDF password.")
            
            self.metadata = doc.metadata
            total_pages = doc.page_count
            logger.info(f"Successfully opened PDF. Pages: {total_pages}")
            
            # Extract text with PyMuPDF for metadata/auth, but we will use pdfplumber for lines
            pymupdf_pages = []
            for i in range(total_pages):
                page = doc[i]
                # We can still get text to detect if layer exists
                text = page.get_text("text")
                pymupdf_pages.append({
                    "page_number": i + 1,
                    "raw_text": text,
                    "raw_lines": [] # Will fill from pdfplumber
                })
                
                # Extract metadata from the first page
                if i == 0:
                    self._extract_statement_metadata(text)
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error processing PDF with PyMuPDF: {e}")
            raise
        
        # 2. Extract lines with pdfplumber
        try:
            with pdfplumber.open(self.pdf_path, password=self.password or "") as pdf:
                if len(pdf.pages) != total_pages:
                    logger.warning("pdfplumber page count differs from PyMuPDF.")
                
                for i, page in enumerate(pdf.pages):
                    if i >= len(pymupdf_pages):
                        break
                    
                    # Extract text line by line using pdfplumber which maintains spatial order well
                    text = page.extract_text()
                    if text:
                        cleaned_lines = self._clean_pymupdf_text(text)
                        pymupdf_pages[i]["raw_lines"] = cleaned_lines
                        pymupdf_pages[i]["raw_text"] = "\n".join(cleaned_lines)
                        
                    # Extract tables (empty if no borders, but keeping logic)
                    tables = page.extract_tables()
                    table_rows = []
                    for table in tables:
                        for row in table:
                            cleaned_row = [str(cell).strip() if cell is not None else None for cell in row]
                            if any(cleaned_row):
                                table_rows.append(cleaned_row)
                    
                    self.pages.append(PageContent(
                        page_number=pymupdf_pages[i]["page_number"],
                        raw_text=pymupdf_pages[i]["raw_text"],
                        raw_lines=pymupdf_pages[i]["raw_lines"],
                        table_rows=table_rows
                    ))
                    
        except Exception as e:
            logger.error(f"Error extracting tables with pdfplumber: {e}")
            # If pdfplumber fails, we fallback to PyMuPDF text
            for i, p_data in enumerate(pymupdf_pages):
                if i >= len(self.pages):
                    cleaned = self._clean_pymupdf_text(p_data["raw_text"])
                    self.pages.append(PageContent(
                        page_number=p_data["page_number"],
                        raw_text="\n".join(cleaned),
                        raw_lines=cleaned,
                        table_rows=[]
                    ))

        return self.pages

    def _clean_pymupdf_text(self, text: str) -> List[str]:
        """Clean up reversed headers, page footers, etc."""
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip reversed watermarks (like 8101-eviL, 5.3V:noisreV)
            if 'eviL' in line or ':noisreV' in line or 'SWSACSMAC' in line:
                continue
                
            # Skip page footer
            if line.startswith("Page ") and " of " in line:
                continue
                
            cleaned.append(line)
            
        return cleaned

    def _extract_statement_metadata(self, text: str) -> None:
        # Extract Period
        period_re = re.compile(r"(\d{2}-[A-Za-z]+-\d{4})\s+To\s+(\d{2}-[A-Za-z]+-\d{4})", re.IGNORECASE)
        m_period = period_re.search(text)
        if m_period:
            try:
                start_date = datetime.strptime(m_period.group(1).strip(), "%d-%b-%Y").date()
                end_date = datetime.strptime(m_period.group(2).strip(), "%d-%b-%Y").date()
                self.statement_metadata["period_start"] = start_date
                self.statement_metadata["period_end"] = end_date
                self.statement_metadata["generated_date"] = end_date # Default to end of period
            except ValueError:
                pass
                
        # Extract Portfolio Summary
        summary_re = re.compile(r"^(.+?(?:Mutual Fund|MUTUAL FUND|Total))\s+([\d,]+\.\d+)\s+([\d,]+\.\d+)$", re.MULTILINE)
        for m in summary_re.finditer(text):
            amc, cost, market = m.groups()
            if "Total" not in amc:
                self.portfolio_summary.append({
                    "amc": amc.strip(),
                    "cost_value": cost.replace(",", ""),
                    "market_value": market.replace(",", "")
                })

