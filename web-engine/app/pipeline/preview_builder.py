from typing import List, Dict, Any
from decimal import Decimal

from app.models.schemas import (
    ImportPreview,
    ImportSummary,
    TransactionBreakdown,
    HoldingPreview,
    ValidationSummary,
    ValidationWarning
)

def build_preview(import_id: str, owner_name: str, pipeline_output: dict, duplicate_risk: bool = False, duplicate_message: str = None) -> ImportPreview:
    statement = pipeline_output["statement"]
    valuation = pipeline_output["valuation"]
    
    # 1. Summary
    nav_data_date = None
    for vh in valuation.valued_holdings:
        if vh.nav_date:
            nav_data_date = vh.nav_date
            break
            
    summary = ImportSummary(
        funds=statement.import_preview.funds_detected,
        folios=statement.import_preview.folios_detected,
        transactions=statement.import_preview.transactions_detected,
        total_current_value=valuation.summary.total_current_value,
        nav_data_date=nav_data_date,
        statement_period_start=statement.statement.period_start,
        statement_period_end=statement.statement.period_end
    )
    
    # 2. Transaction Breakdown
    tx_bdown = TransactionBreakdown(
        purchases=statement.import_preview.purchase_transactions,
        redemptions=statement.import_preview.redemption_transactions,
        switches=statement.import_preview.switch_transactions,
        reversals=statement.import_preview.reversal_transactions,
        stamp_duty=statement.import_preview.stamp_duty_transactions,
        other=statement.import_preview.other_transactions
    )
    
    # 3. Holdings
    holdings: List[HoldingPreview] = []
    
    # Map scheme_name to folios from reconstruction
    reconstruction = pipeline_output["reconstruction"]
    scheme_to_folios = {}
    for folio_holding in reconstruction.folios:
        s_name = folio_holding.scheme_name
        if s_name not in scheme_to_folios:
            scheme_to_folios[s_name] = set()
        scheme_to_folios[s_name].add(folio_holding.folio_number)
            
    for vh in valuation.valued_holdings:
        folios = list(scheme_to_folios.get(vh.scheme_name, []))
        nav = vh.nav_record.nav if vh.nav_record else None
        
        h_preview = HoldingPreview(
            scheme_name=vh.scheme_name,
            amc=vh.mapping.amc,
            isin=vh.mapping.cas_isin,
            folios=folios,
            total_units=vh.total_units,
            nav=nav,
            nav_date=vh.nav_date,
            current_value=vh.current_value,
            nav_status=vh.nav_status.value,
            mapping_method=vh.mapping.match_method
        )
        holdings.append(h_preview)
        
    # 4. Validation
    warnings = []
    for w in statement.validation.warnings:
        warnings.append(ValidationWarning(
            folio=w.folio_number,
            transaction_date=w.date,
            message=w.message
        ))
        
    validation = ValidationSummary(
        parser_warnings=len(statement.validation.warnings),
        reconciliation_warnings=reconstruction.reconciliation_summary.folios_failed,
        nav_errors=valuation.summary.schemes_error,
        unmatched_schemes=valuation.summary.schemes_unmatched,
        stale_nav_schemes=0,  # Could be derived from nav_status
        warnings=warnings
    )
    
    preview = ImportPreview(
        import_id=import_id,
        portfolio_owner=owner_name,
        status="PREVIEW_READY",
        duplicate_risk=duplicate_risk,
        duplicate_message=duplicate_message,
        summary=summary,
        transaction_breakdown=tx_bdown,
        holdings=holdings,
        validation=validation
    )
    
    return preview
