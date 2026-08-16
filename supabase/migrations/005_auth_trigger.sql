-- Create a trigger function to initialize user and default portfolio
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  new_portfolio_id UUID;
BEGIN
  -- 1. Insert into public.users
  INSERT INTO public.users (id, display_name)
  VALUES (new.id, COALESCE(new.raw_user_meta_data->>'name', 'New User'));

  -- 2. Create a default portfolio
  INSERT INTO public.portfolios (owner_user_id, name)
  VALUES (new.id, 'My Portfolio')
  RETURNING id INTO new_portfolio_id;

  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create the trigger
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
