from decimal import Decimal

from app.engine.scheme import aggregate_by_scheme
from app.models.holding import FolioHolding, FolioReconciliation, ReconciliationStatus


def create_mock_folio(folio_num: str, scheme: str, units: str) -> FolioHolding:
    return FolioHolding(
        folio_number=folio_num,
        amc="Test AMC",
        registrar="CAMS",
        scheme_name=scheme,
        opening_units=Decimal("0.000"),
        calculated_closing_units=Decimal(units),
        gross_purchases=Decimal("0"),
        gross_redemptions=Decimal("0"),
        gross_reversals=Decimal("0"),
        stamp_duty=Decimal("0"),
        net_cash_flow=Decimal("0"),
        reconciliation=FolioReconciliation(
            cas_closing_units=Decimal(units),
            calculated_closing_units=Decimal(units),
            difference=Decimal("0.000"),
            status=ReconciliationStatus.PASS
        )
    )


def test_single_folio_aggregation():
    folios = [
        create_mock_folio("123", "Scheme A", "10.000")
    ]
    
    schemes = aggregate_by_scheme(folios)
    
    assert len(schemes) == 1
    assert schemes[0].scheme_name == "Scheme A"
    assert schemes[0].total_units == Decimal("10.000")
    assert schemes[0].folios == ["123"]


def test_multiple_folios_same_scheme():
    folios = [
        create_mock_folio("123", "Motilal Oswal", "4730.983"),
        create_mock_folio("456", "Motilal Oswal", "2267.433")
    ]
    
    schemes = aggregate_by_scheme(folios)
    
    assert len(schemes) == 1
    assert schemes[0].scheme_name == "Motilal Oswal"
    assert schemes[0].total_units == Decimal("6998.416")
    assert schemes[0].folios == ["123", "456"]


def test_multiple_different_schemes():
    folios = [
        create_mock_folio("123", "Scheme A", "10.000"),
        create_mock_folio("456", "Scheme B", "20.000")
    ]
    
    schemes = aggregate_by_scheme(folios)
    
    assert len(schemes) == 2
    names = [s.scheme_name for s in schemes]
    assert "Scheme A" in names
    assert "Scheme B" in names
