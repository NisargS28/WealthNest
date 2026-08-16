-- Drop the recursive policy on families
DROP POLICY IF EXISTS "Family members can view their families" ON families;

-- Create a security definer function to check family membership bypassing RLS
CREATE OR REPLACE FUNCTION public.is_family_member(fam_id UUID, usr_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.family_members
    WHERE family_id = fam_id AND user_id = usr_id
  );
$$ LANGUAGE sql SECURITY DEFINER;

-- Recreate the policy using the security definer function to break recursion
CREATE POLICY "Family members can view their families" ON families FOR SELECT USING (
  public.is_family_member(id, auth.uid())
);
