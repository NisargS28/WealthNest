import logging
from typing import Optional
from app.db.supabase import get_supabase_client
from app.models.schemas import FamilyMemberBase

logger = logging.getLogger(__name__)

class FamilyService:
    def __init__(self, token: Optional[str] = None):
        self.supabase = get_supabase_client(token)

    def get_members(self) -> list[FamilyMemberBase]:
        res = self.supabase.table("family_members").select("*").order("created_at").execute()
        return [FamilyMemberBase(
            id=m["id"],
            display_name=m["display_name"],
            created_at=m["created_at"]
        ) for m in res.data]

    def create_member(self, display_name: str, user_id: str) -> FamilyMemberBase:
        # Create the family member
        data = {
            "display_name": display_name,
            "owner_user_id": user_id
        }
        res = self.supabase.table("family_members").insert(data).execute()
        if not res.data:
            raise ValueError("Failed to create family member")
        
        m = res.data[0]
        member_id = m["id"]

        # Create a default portfolio for this member
        port_data = {
            "member_id": member_id,
            "owner_user_id": user_id,
            "display_name": f"{display_name}'s Portfolio"
        }
        self.supabase.table("portfolios").insert(port_data).execute()

        return FamilyMemberBase(
            id=m["id"],
            display_name=m["display_name"],
            created_at=m["created_at"]
        )

