import os
import logging
import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.api.auth import get_auth_token
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)


@router.get("/notifications")
def get_notifications(token: Optional[str] = Depends(get_auth_token)):
    """Returns all notifications for the authenticated user, newest first."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    supabase = get_supabase_client(token)
    try:
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = user.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth failed: {str(e)}")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                n.id, n.type, n.title, n.message, n.entity_type, n.entity_id,
                n.status, n.created_at,
                -- SIP plan data (for SIP_PLAN_DETECTED)
                sp.sip_day,
                sp.amount AS sip_amount,
                sp.frequency,
                sp.next_expected_date,
                sp.status AS sip_status,
                CASE WHEN n.entity_type = 'sip_plan' THEN s.scheme_name
                     WHEN n.entity_type = 'sip_occurrence' THEN s2.scheme_name
                END AS scheme_name,
                -- SIP occurrence data (for SIP_CONFIRMATION)
                so.expected_date AS occurrence_expected_date,
                so.amount AS occurrence_amount,
                so.status AS occurrence_status
            FROM public.notifications n
            LEFT JOIN public.sip_plans sp
                ON n.entity_type = 'sip_plan' AND sp.id = n.entity_id
            LEFT JOIN public.schemes s ON sp.scheme_id = s.id
            LEFT JOIN public.sip_occurrences so
                ON n.entity_type = 'sip_occurrence' AND so.id = n.entity_id
            LEFT JOIN public.sip_plans sp2 ON so.sip_plan_id = sp2.id
            LEFT JOIN public.schemes s2 ON sp2.scheme_id = s2.id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        notifications = []
        for row in rows:
            obj = dict(zip(cols, row))
            # Serialize dates/decimals
            for k, v in obj.items():
                if hasattr(v, 'isoformat'):
                    obj[k] = v.isoformat()
                elif hasattr(v, '__float__') and type(v).__name__ == 'Decimal':
                    obj[k] = float(v)
            notifications.append(obj)
        return {"notifications": notifications, "unread_count": sum(1 for n in notifications if n["status"] == "UNREAD")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, token: Optional[str] = Depends(get_auth_token)):
    """Marks a single notification as READ."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE public.notifications
            SET status = 'READ', read_at = NOW()
            WHERE id = %s
        """, (notification_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
