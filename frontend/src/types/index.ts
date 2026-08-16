export interface FamilyMember {
  id: string;
  display_name: string;
  created_at: string;
}

export interface PortfolioSummary {
  id: string;
  member_id: string;
  display_name: string;
  created_at: string;
  total_current_value: string | null;
  last_valuation_date: string | null;
  folio_count: number;
  transaction_count: number;
}

export type ImportStatus =
  | "UPLOADED" | "PARSING" | "PARSED"
  | "RECONSTRUCTED" | "VALUED" | "PREVIEW_READY"
  | "CONFIRMED" | "FAILED" | "CANCELLED";

export type NavStatus =
  | "AVAILABLE" | "NAV_UNAVAILABLE" | "SCHEME_UNMATCHED"
  | "AMBIGUOUS" | "API_ERROR" | "STALE_DATA";

export interface ImportSessionResponse {
  import_id: string;
  status: ImportStatus;
  preview?: ImportPreview;
  error_message?: string;
}

export interface ImportPreview {
  import_id: string;
  portfolio_owner: string;
  status: ImportStatus;
  duplicate_risk: boolean;
  duplicate_message: string | null;
  summary: ImportSummary;
  transaction_breakdown: TransactionBreakdown;
  holdings: HoldingPreview[];
  validation: ValidationSummary;
}

export interface ImportSummary {
  funds: number;
  folios: number;
  transactions: number;
  total_current_value: string;
  nav_data_date: string | null;
  statement_period_start: string | null;
  statement_period_end: string | null;
}

export interface TransactionBreakdown {
  purchases: number;
  redemptions: number;
  switches: number;
  reversals: number;
  stamp_duty: number;
  other: number;
}

export interface HoldingPreview {
  scheme_name: string;
  amc: string;
  isin: string | null;
  folios: string[];
  total_units: string;
  nav: string | null;
  nav_date: string | null;
  current_value: string | null;
  nav_status: NavStatus;
  mapping_method: string | null;
}

export interface ValidationSummary {
  parser_warnings: number;
  reconciliation_warnings: number;
  nav_errors: number;
  unmatched_schemes: number;
  stale_nav_schemes: number;
  warnings: ValidationWarning[];
}

export interface ValidationWarning {
  folio: string;
  transaction_date: string;
  message: string;
}

export interface PortfolioDetail {
  id: string;
  member_id: string;
  display_name: string;
  holdings: StoredHolding[];
  folios: StoredFolio[];
  valuation: ValuationDetail | null;
}

export interface StoredHolding {
  scheme_name: string;
  amc: string;
  isin: string | null;
  total_units: string;
  current_value: string | null;
  nav: string | null;
  nav_date: string | null;
  nav_status: NavStatus;
  folios: string[];
}

export interface StoredFolio {
  folio_number: string;
  amc: string;
  scheme_name: string;
  isin: string | null;
  opening_units: string;
  cas_closing_units: string | null;
  transaction_count: number;
}

export interface Transaction {
  id: string;
  date: string;
  transaction_type: string;
  subtype: string | null;
  description: string;
  amount: string | null;
  units: string | null;
  nav: string | null;
  unit_balance: string | null;
  is_sip: boolean;
}

export interface ValuationDetail {
  portfolio_id: string;
  generated_at: string;
  total_current_value: string;
  holdings: StoredHolding[];
}

export interface FamilyView {
  members: FamilyMember[];
  aggregate: {
    total_value: string;
    member_summaries: PortfolioSummary[];
  };
}

export interface HoldingDetail {
  id: string;
  scheme_name: string;
  folio_number: string;
  amc_name: string;
  category: string | null;
  invested: string;
  current_value: string;
  returns: string;
  nav: string;
  units: string;
  nav_date: string | null;
}

export interface AssetAllocation {
  name: string;
  value: string;
  color: string;
}

export interface ValuationHistory {
  month: string;
  value: string;
  invested: string;
}

export interface DashboardResponse {
  total_value: string;
  total_invested: string;
  profit_loss: string;
  profit_percentage: string;
  portfolio_count: number;
  recent_transactions: Transaction[];
  top_holdings: HoldingDetail[];
  asset_allocation: AssetAllocation[];
  pending_actions: number;
  valuation_history: ValuationHistory[];
}
