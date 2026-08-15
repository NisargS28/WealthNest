import argparse
import json
import logging
import sys
import os

from app.provider.mfapi import MFAPIProvider
from app.mapper.scheme_master import SchemeMasterIndex
from app.mapper.scheme_mapper import SchemeMapper
from app.cache.nav_cache import NAVCache
from app.valuation.engine import ValuationEngine
from app.models.nav import ValuationResult

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate_text_report(result: ValuationResult, report_path: str):
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"WEALTHNEST VALUATION REPORT\n")
        f.write(f"Generated at: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source file : {result.source_file}\n")
        f.write("=" * 60 + "\n\n")

        sum = result.summary
        f.write("--- VALUATION SUMMARY ---\n")
        f.write(f"Schemes Total         : {sum.schemes_total}\n")
        f.write(f"Schemes Valued        : {sum.schemes_valued}\n")
        f.write(f"Schemes Unmatched     : {sum.schemes_unmatched}\n")
        f.write(f"Schemes Error         : {sum.schemes_error}\n")
        f.write(f"Schemes Unavailable   : {sum.unavailable_value_schemes}\n")
        f.write(f"Total Current Value   : INR {sum.total_current_value:,.2f}\n")
        f.write("-" * 60 + "\n\n")

        for vh in result.valued_holdings:
            f.write(f"Scheme : {vh.scheme_name}\n")
            f.write(f"Units  : {vh.total_units}\n")
            f.write(f"Mapping: {vh.mapping.status.value} (Method: {vh.mapping.match_method})\n")
            f.write(f"Status : {vh.nav_status.value}\n")
            
            if vh.current_value is not None:
                f.write(f"NAV    : {vh.nav_record.nav} (Date: {vh.nav_date})\n")
                f.write(f"Value  : INR {vh.current_value:,.2f}\n")
            else:
                f.write(f"Value  : UNAVAILABLE\n")
                
            f.write("-" * 40 + "\n")


def main():
    parser = argparse.ArgumentParser(description="WealthNest NAV Valuation Engine (v0.3)")
    parser.add_argument("--input", "-i", required=True, help="Path to portfolio_reconstructed.json")
    parser.add_argument("--output", "-o", required=True, help="Path to save portfolio_valued.json")
    parser.add_argument("--report", "-r", required=False, help="Path to save text report")
    
    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        reconstructed = json.load(f)

    # Initialize components
    provider = MFAPIProvider()
    master = SchemeMasterIndex(provider)
    mapper = SchemeMapper(provider, master)
    cache = NAVCache()
    engine = ValuationEngine(provider, mapper, cache)

    # Value portfolio
    logger.info("Starting portfolio valuation...")
    result = engine.value_portfolio(reconstructed)

    # Save JSON
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(args.output, "w", encoding="utf-8") as f:
        # pydantic v2 dump
        data = result.model_dump(mode="json")
        json.dump(data, f, indent=2)

    logger.info(f"Saved valued portfolio to {args.output}")

    if args.report:
        rep_dir = os.path.dirname(args.report)
        if rep_dir and not os.path.exists(rep_dir):
            os.makedirs(rep_dir)
        generate_text_report(result, args.report)
        logger.info(f"Saved text report to {args.report}")


if __name__ == "__main__":
    main()
