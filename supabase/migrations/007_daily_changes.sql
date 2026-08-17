ALTER TABLE public.portfolio_valuations 
ADD COLUMN IF NOT EXISTS one_day_change NUMERIC,
ADD COLUMN IF NOT EXISTS one_day_change_percent NUMERIC;
