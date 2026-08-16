DROP POLICY IF EXISTS "Users can insert own record" ON users;
-- Allow users to insert their own profile upon signup
CREATE POLICY "Users can insert own record" ON users FOR INSERT WITH CHECK (auth.uid() = id);
