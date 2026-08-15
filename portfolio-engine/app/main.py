import argparse
import json
import os
from datetime import datetime, timezone

from app.engine.loader import load_parsed_cas
from app.engine.folio import reconstruct_folio, UNIT_TOLERANCE
from app.engine.scheme import aggregate_by_scheme
from app.models.holding import (
    PortfolioReconstruction,
    ReconciliationSummary,
    ReconciliationStatus
)
from app.reporter import generate_report


def main():
    parser = argparse.ArgumentParser(description="WealthNest Portfolio Reconstruction Engine")
    parser.add_argument("--input", required=True, help="Path to parsed_cas.json")
    parser.add_argument("--output", required=True, help="Path to output portfolio_reconstructed.json")
    parser.add_argument("--report", required=False, help="Path to output plain-text reconciliation report")
    
    args = parser.parse_args()
    
    # 1. Load parsed CAS
    cas_data = load_parsed_cas(args.input)
    
    # 2. Reconstruct Folios
    folios_raw = cas_data.get("folios", [])
    folio_holdings = []
    
    for folio_raw in folios_raw:
        holding = reconstruct_folio(folio_raw)
        folio_holdings.append(holding)
        
    # 3. Aggregate by Scheme
    scheme_holdings = aggregate_by_scheme(folio_holdings)
    
    # 4. Summarize Reconciliation
    passed = sum(1 for f in folio_holdings if f.reconciliation.status == ReconciliationStatus.PASS)
    failed = sum(1 for f in folio_holdings if f.reconciliation.status == ReconciliationStatus.FAIL)
    
    summary = ReconciliationSummary(
        folios_processed=len(folio_holdings),
        folios_passed=passed,
        folios_failed=failed,
        unit_tolerance=UNIT_TOLERANCE
    )
    
    # 5. Build Final Output
    reconstruction = PortfolioReconstruction(
        source_file=os.path.basename(args.input),
        generated_at=datetime.now(timezone.utc),
        folios=folio_holdings,
        scheme_holdings=scheme_holdings,
        reconciliation_summary=summary
    )
    
    # 6. Save JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        # Use Pydantic's model_dump_json for proper Decimal serialization
        f.write(reconstruction.model_dump_json(indent=2))
        
    print(f"Reconstructed portfolio saved to: {args.output}")
    
    # 7. Generate Text Report
    report_text = generate_report(reconstruction)
    if args.report:
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"Reconciliation report saved to: {args.report}")
    else:
        print("\n" + report_text)


if __name__ == "__main__":
    main()
