import argparse
import getpass
import json
import logging
import sys
from datetime import date
from decimal import Decimal

from app.models.statement import Statement, ImportPreview, StatementMetadata, ValidationSummary, UnparsedTransaction, PortfolioSummaryRow
from app.parser.pdf_reader import PdfReader
from app.parser.section_detector import SectionDetector
from app.parser.fund_parser import FundParser
from app.parser.transaction_parser import TransactionParser
from app.parser.validator import Validator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, date):
            return obj.isoformat()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)

def main():
    parser = argparse.ArgumentParser(description="Parse CAMS+KFintech CAS PDF into JSON")
    parser.add_argument("--input", "-i", required=True, help="Path to the CAS PDF file")
    parser.add_argument("--output", "-o", default="output/parsed_cas.json", help="Output JSON path")
    parser.add_argument("--password", "-p", nargs="?", const=True, help="PDF Password (if not provided, will prompt)")
    
    args = parser.parse_args()
    
    password = None
    if args.password is True:
        password = getpass.getpass("Enter PDF Password: ")
    elif isinstance(args.password, str):
        password = args.password
        
    try:
        # Initialize parsers
        pdf_reader = PdfReader(args.input, password)
        section_detector = SectionDetector()
        fund_parser = FundParser()
        tx_parser = TransactionParser()
        validator = Validator()
        
        # 1. Read PDF
        pages = pdf_reader.process()
        
        # 2. Split into sections
        sections = section_detector.extract_sections(pages)
        
        # 3. Process each section
        statement = Statement()
        
        # Extract statement metadata
        statement.statement.period_start = pdf_reader.statement_metadata["period_start"]
        statement.statement.period_end = pdf_reader.statement_metadata["period_end"]
        statement.statement.generated_date = pdf_reader.statement_metadata["generated_date"]
        
        # Add portfolio summary
        for sum_item in pdf_reader.portfolio_summary:
            statement.portfolio_summary.append(PortfolioSummaryRow(
                amc=sum_item["amc"],
                cost_value=Decimal(sum_item["cost_value"]),
                market_value=Decimal(sum_item["market_value"])
            ))
        
        for section in sections:
            # Parse Fund metadata
            folio = fund_parser.parse(section)
            
            # Parse Transactions
            transactions = tx_parser.parse_transactions(section.raw_lines, statement.unparsed_transactions)
            folio.transactions = transactions
            
            # Validate
            warnings = validator.validate(folio)
            statement.validation.warnings.extend(warnings)
            
            statement.folios.append(folio)
            
        # 4. Generate Import Preview
        preview = ImportPreview()
        preview.folios_detected = len(statement.folios)
        preview.funds_detected = len({f.scheme_name for f in statement.folios})
        
        for f in statement.folios:
            preview.transactions_detected += len(f.transactions)
            for tx in f.transactions:
                if tx.transaction_type.name == "PURCHASE":
                    preview.purchase_transactions += 1
                elif tx.transaction_type.name == "REDEMPTION":
                    preview.redemption_transactions += 1
                elif tx.transaction_type.name == "SWITCH_IN" or tx.transaction_type.name == "SWITCH_OUT":
                    preview.switch_transactions += 1
                elif tx.transaction_type.name == "STAMP_DUTY":
                    preview.stamp_duty_transactions += 1
                elif tx.transaction_type.name == "REVERSAL":
                    preview.reversal_transactions += 1
                else:
                    preview.other_transactions += 1
                    
            # Note: SIP patterns removed as per user request
            
        statement.import_preview = preview
        
        # 5. Output JSON
        import os
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(statement.model_dump(), f, cls=JSONEncoder, indent=2)
            
        # 6. Print Summary
        print("\nCAS Parsing Completed")
        print("-----------------------------")
        print(f"Funds detected:       {preview.funds_detected:>3}")
        print(f"Folios detected:      {preview.folios_detected:>3}")
        print(f"Transactions:         {preview.transactions_detected:>3}")
        print(f"  Parsed:             {preview.transactions_detected - len(statement.unparsed_transactions):>3}")
        print(f"    Purchases:        {preview.purchase_transactions:>3}")
        print(f"    Reversals:        {preview.reversal_transactions:>3}")
        print(f"    Stamp Duty:       {preview.stamp_duty_transactions:>3}")
        print(f"    Other/Switches:   {preview.other_transactions + preview.switch_transactions + preview.redemption_transactions:>3}")
        print(f"  Needs review:       {len(statement.unparsed_transactions):>3}")
        if statement.validation.warnings:
            print(f"Validation Warnings:  {len(statement.validation.warnings):>3}")
        print("-----------------------------")
        print(f"Output: {args.output}")
        
    except Exception as e:
        logger.exception("Parsing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
