-- Indexes for commonly queried foreign keys and dates

CREATE INDEX idx_portfolios_owner ON portfolios(owner_user_id);
CREATE INDEX idx_families_creator ON families(created_by_user_id);
CREATE INDEX idx_family_members_family ON family_members(family_id);
CREATE INDEX idx_family_members_user ON family_members(user_id);
CREATE INDEX idx_assets_portfolio ON assets(portfolio_id);
CREATE INDEX idx_folios_asset ON folios(asset_id);
CREATE INDEX idx_folios_scheme ON folios(scheme_id);
CREATE INDEX idx_imports_portfolio ON imports(portfolio_id);
CREATE INDEX idx_import_tx_import ON import_transactions(import_id);
CREATE INDEX idx_tx_folio ON transactions(folio_id);
CREATE INDEX idx_tx_scheme ON transactions(scheme_id);
CREATE INDEX idx_tx_import ON transactions(import_id);
CREATE INDEX idx_sip_plans_portfolio ON sip_plans(portfolio_id);
CREATE INDEX idx_sip_occurrences_plan ON sip_occurrences(sip_plan_id);
CREATE INDEX idx_nav_records_scheme ON nav_records(scheme_id);
CREATE INDEX idx_nav_records_date ON nav_records(nav_date);
CREATE INDEX idx_valuations_portfolio ON portfolio_valuations(portfolio_id);
CREATE INDEX idx_valuations_date ON portfolio_valuations(valuation_date);
CREATE INDEX idx_valuation_holdings_val ON portfolio_valuation_holdings(valuation_id);
CREATE INDEX idx_notifications_user ON notifications(user_id);

-- Sensible CHECK constraints for statuses
ALTER TABLE imports ADD CONSTRAINT chk_imports_status 
  CHECK (status IN ('UPLOADED', 'PARSING', 'PREVIEW_READY', 'CONFIRMED', 'FAILED', 'CANCELLED'));

ALTER TABLE sip_occurrences ADD CONSTRAINT chk_sip_occ_status 
  CHECK (status IN ('PENDING', 'CONFIRMED', 'DECLINED'));

ALTER TABLE notifications ADD CONSTRAINT chk_notification_type
  CHECK (type IN ('SIP_CONFIRMATION', 'NEW_INVESTMENT', 'IMPORT_COMPLETED', 'IMPORT_FAILED', 'IMPORT_REVIEW', 'NAV_UNAVAILABLE', 'NAV_STALE', 'SYSTEM'));
