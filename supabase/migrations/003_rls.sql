-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE families ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE folios ENABLE ROW LEVEL SECURITY;
ALTER TABLE imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sip_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE sip_occurrences ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_valuation_holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- 1. Users
CREATE POLICY "Users can view own record" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own record" ON users FOR UPDATE USING (auth.uid() = id);

-- 2. Families
CREATE POLICY "Users can manage families they created" ON families FOR ALL USING (auth.uid() = created_by_user_id);
CREATE POLICY "Family members can view their families" ON families FOR SELECT USING (
  EXISTS (SELECT 1 FROM family_members WHERE family_id = families.id AND user_id = auth.uid())
);

-- 3. Family Members
CREATE POLICY "Family creators can manage members" ON family_members FOR ALL USING (
  EXISTS (SELECT 1 FROM families WHERE id = family_members.family_id AND created_by_user_id = auth.uid())
);
CREATE POLICY "Members can view their own membership" ON family_members FOR SELECT USING (user_id = auth.uid());

-- 4. Family Portfolios
CREATE POLICY "Family creators can manage family portfolios" ON family_portfolios FOR ALL USING (
  EXISTS (SELECT 1 FROM families WHERE id = family_portfolios.family_id AND created_by_user_id = auth.uid())
);
CREATE POLICY "Members can view family portfolios" ON family_portfolios FOR SELECT USING (
  EXISTS (SELECT 1 FROM family_members WHERE family_id = family_portfolios.family_id AND user_id = auth.uid())
);

-- 5. Portfolios
CREATE POLICY "Users can manage own portfolios" ON portfolios FOR ALL USING (auth.uid() = owner_user_id);
CREATE POLICY "Family members can view shared portfolios" ON portfolios FOR SELECT USING (
  EXISTS (SELECT 1 FROM family_portfolios fp 
          JOIN family_members fm ON fp.family_id = fm.family_id 
          WHERE fp.portfolio_id = portfolios.id AND fm.user_id = auth.uid())
);

-- 6. Assets
CREATE POLICY "Users can manage own assets" ON assets FOR ALL USING (
  EXISTS (SELECT 1 FROM portfolios p WHERE p.id = assets.portfolio_id AND p.owner_user_id = auth.uid())
);
CREATE POLICY "Family members can view shared assets" ON assets FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM portfolios p 
    JOIN family_portfolios fp ON p.id = fp.portfolio_id
    JOIN family_members fm ON fp.family_id = fm.family_id
    WHERE p.id = assets.portfolio_id AND fm.user_id = auth.uid()
  )
);

-- 7. Folios
CREATE POLICY "Users can manage own folios" ON folios FOR ALL USING (
  EXISTS (SELECT 1 FROM assets a JOIN portfolios p ON a.portfolio_id = p.id 
          WHERE a.id = folios.asset_id AND p.owner_user_id = auth.uid())
);
CREATE POLICY "Family members can view shared folios" ON folios FOR SELECT USING (
  EXISTS (SELECT 1 FROM assets a JOIN portfolios p ON a.portfolio_id = p.id
          JOIN family_portfolios fp ON p.id = fp.portfolio_id
          JOIN family_members fm ON fp.family_id = fm.family_id
          WHERE a.id = folios.asset_id AND fm.user_id = auth.uid())
);

-- 8. Transactions
CREATE POLICY "Users can manage own transactions" ON transactions FOR ALL USING (
  EXISTS (SELECT 1 FROM folios f JOIN assets a ON f.asset_id = a.id 
          JOIN portfolios p ON a.portfolio_id = p.id 
          WHERE f.id = transactions.folio_id AND p.owner_user_id = auth.uid())
);
CREATE POLICY "Family members can view shared transactions" ON transactions FOR SELECT USING (
  EXISTS (SELECT 1 FROM folios f JOIN assets a ON f.asset_id = a.id 
          JOIN portfolios p ON a.portfolio_id = p.id
          JOIN family_portfolios fp ON p.id = fp.portfolio_id
          JOIN family_members fm ON fp.family_id = fm.family_id
          WHERE f.id = transactions.folio_id AND fm.user_id = auth.uid())
);

-- 9. Imports
CREATE POLICY "Users can manage own imports" ON imports FOR ALL USING (auth.uid() = uploaded_by_user_id);

-- 10. Import Transactions
CREATE POLICY "Users can manage own import transactions" ON import_transactions FOR ALL USING (
  EXISTS (SELECT 1 FROM imports i WHERE i.id = import_transactions.import_id AND i.uploaded_by_user_id = auth.uid())
);

-- 11. SIP Plans
CREATE POLICY "Users can manage own SIP plans" ON sip_plans FOR ALL USING (
  EXISTS (SELECT 1 FROM portfolios p WHERE p.id = sip_plans.portfolio_id AND p.owner_user_id = auth.uid())
);

-- 12. SIP Occurrences
CREATE POLICY "Users can manage own SIP occurrences" ON sip_occurrences FOR ALL USING (
  EXISTS (SELECT 1 FROM sip_plans sp JOIN portfolios p ON sp.portfolio_id = p.id 
          WHERE sp.id = sip_occurrences.sip_plan_id AND p.owner_user_id = auth.uid())
);

-- 13. Portfolio Valuations
CREATE POLICY "Users can view own valuations" ON portfolio_valuations FOR ALL USING (
  EXISTS (SELECT 1 FROM portfolios p WHERE p.id = portfolio_valuations.portfolio_id AND p.owner_user_id = auth.uid())
);
CREATE POLICY "Family members can view shared valuations" ON portfolio_valuations FOR SELECT USING (
  EXISTS (SELECT 1 FROM portfolios p
          JOIN family_portfolios fp ON p.id = fp.portfolio_id
          JOIN family_members fm ON fp.family_id = fm.family_id
          WHERE p.id = portfolio_valuations.portfolio_id AND fm.user_id = auth.uid())
);

-- 14. Valuation Holdings
CREATE POLICY "Users can view own valuation holdings" ON portfolio_valuation_holdings FOR ALL USING (
  EXISTS (SELECT 1 FROM portfolio_valuations pv JOIN portfolios p ON pv.portfolio_id = p.id 
          WHERE pv.id = portfolio_valuation_holdings.valuation_id AND p.owner_user_id = auth.uid())
);
CREATE POLICY "Family members can view shared valuation holdings" ON portfolio_valuation_holdings FOR SELECT USING (
  EXISTS (SELECT 1 FROM portfolio_valuations pv
          JOIN portfolios p ON pv.portfolio_id = p.id 
          JOIN family_portfolios fp ON p.id = fp.portfolio_id
          JOIN family_members fm ON fp.family_id = fm.family_id
          WHERE pv.id = portfolio_valuation_holdings.valuation_id AND fm.user_id = auth.uid())
);

-- 15. Notifications
CREATE POLICY "Users can manage own notifications" ON notifications FOR ALL USING (auth.uid() = user_id);

-- 16. Schemes (Public read-only)
CREATE POLICY "Anyone can read schemes" ON schemes FOR SELECT USING (true);

-- 17. NAV Records (Public read-only)
CREATE POLICY "Anyone can read nav records" ON nav_records FOR SELECT USING (true);
