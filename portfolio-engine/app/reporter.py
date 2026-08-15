from app.models.holding import PortfolioReconstruction


def generate_report(reconstruction: PortfolioReconstruction) -> str:
    """
    Generates a human-readable text report from the PortfolioReconstruction object.
    """
    lines = []
    lines.append("WealthNest Portfolio Reconstruction Report")
    lines.append("==========================================")
    lines.append(f"Source: {reconstruction.source_file}")
    lines.append(f"Generated: {reconstruction.generated_at.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    lines.append("Folio Reconciliation")
    lines.append("--------------------")
    for folio in reconstruction.folios:
        status_tag = f"[{folio.reconciliation.status.value}]"
        lines.append(f"{status_tag} {folio.folio_number} — {folio.scheme_name}")
        lines.append(f"  Opening:    {folio.opening_units}")
        lines.append(f"  Calculated: {folio.calculated_closing_units}")
        if folio.cas_closing_units is not None:
            lines.append(f"  CAS:        {folio.cas_closing_units}")
            lines.append(f"  Difference: {folio.reconciliation.difference}")
        else:
            lines.append("  CAS:        None (No closing balance provided)")
        lines.append("")

    lines.append("Scheme Aggregation")
    lines.append("------------------")
    for scheme in reconstruction.scheme_holdings:
        lines.append(f"{scheme.scheme_name}")
        for folio_num in scheme.folios:
            # Find the holding to display its units
            folio_holding = next(f for f in reconstruction.folios if f.folio_number == folio_num)
            lines.append(f"  Folio {folio_num}: {folio_holding.calculated_closing_units} units")
        lines.append(f"  Total:             {scheme.total_units} units")
        lines.append("")
        
    summary = reconstruction.reconciliation_summary
    lines.append(f"Summary: {summary.folios_passed}/{summary.folios_processed} folios PASS")
    
    return "\n".join(lines) + "\n"
