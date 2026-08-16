CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  base_currency CHAR(3) DEFAULT 'INR',
  status TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE families (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_by_user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE family_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID REFERENCES families(id) ON DELETE CASCADE,
  user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  relationship TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE family_portfolios (
  family_id UUID REFERENCES families(id) ON DELETE CASCADE,
  member_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
  portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (family_id, portfolio_id)
);

CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID REFERENCES portfolios(id),
  asset_type TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE schemes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  isin TEXT,
  amfi_code TEXT,
  scheme_name TEXT NOT NULL,
  amc_name TEXT,
  plan TEXT,
  option TEXT,
  provider TEXT,
  provider_scheme_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE folios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID REFERENCES assets(id),
  scheme_id UUID REFERENCES schemes(id),
  folio_number TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE imports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID REFERENCES portfolios(id),
  uploaded_by_user_id UUID REFERENCES users(id),
  source_type TEXT,
  filename TEXT,
  statement_start DATE,
  statement_end DATE,
  generated_date DATE,
  parser_name TEXT,
  parser_version TEXT,
  status TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  confirmed_at TIMESTAMPTZ NULL,
  error_code TEXT NULL,
  error_message TEXT NULL
);

CREATE TABLE import_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  import_id UUID REFERENCES imports(id) ON DELETE CASCADE,
  folio_number TEXT,
  scheme_name TEXT,
  isin TEXT,
  transaction_date DATE,
  transaction_type TEXT,
  transaction_subtype TEXT,
  description TEXT,
  amount NUMERIC,
  units NUMERIC,
  nav NUMERIC,
  unit_balance NUMERIC,
  fingerprint TEXT,
  classification TEXT,
  validation_status TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  folio_id UUID REFERENCES folios(id),
  scheme_id UUID REFERENCES schemes(id),
  import_id UUID NULL REFERENCES imports(id) ON DELETE SET NULL,
  transaction_date DATE NOT NULL,
  transaction_type TEXT NOT NULL,
  transaction_subtype TEXT,
  description TEXT,
  amount NUMERIC,
  units NUMERIC,
  nav NUMERIC,
  unit_balance NUMERIC,
  source_type TEXT NOT NULL,
  fingerprint TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sip_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID REFERENCES portfolios(id),
  folio_id UUID REFERENCES folios(id),
  scheme_id UUID REFERENCES schemes(id),
  amount NUMERIC NOT NULL,
  frequency TEXT NOT NULL,
  sip_day INTEGER,
  start_date DATE NOT NULL,
  next_expected_date DATE,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sip_occurrences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sip_plan_id UUID REFERENCES sip_plans(id),
  expected_date DATE NOT NULL,
  actual_date DATE NULL,
  amount NUMERIC NOT NULL,
  status TEXT NOT NULL,
  transaction_id UUID NULL REFERENCES transactions(id) ON DELETE SET NULL,
  confirmed_by_user_id UUID NULL REFERENCES users(id),
  confirmed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE nav_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scheme_id UUID REFERENCES schemes(id),
  provider TEXT,
  provider_scheme_id TEXT,
  nav NUMERIC NOT NULL,
  nav_date DATE NOT NULL,
  fetched_at TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE portfolio_valuations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  portfolio_id UUID REFERENCES portfolios(id),
  valuation_date DATE NOT NULL,
  total_value NUMERIC NOT NULL,
  total_cost NUMERIC,
  total_profit NUMERIC,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE portfolio_valuation_holdings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  valuation_id UUID REFERENCES portfolio_valuations(id) ON DELETE CASCADE,
  asset_id UUID REFERENCES assets(id),
  units NUMERIC NOT NULL,
  nav NUMERIC,
  nav_date DATE,
  market_value NUMERIC NOT NULL,
  status TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  entity_type TEXT NULL,
  entity_id UUID NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  read_at TIMESTAMPTZ NULL
);
