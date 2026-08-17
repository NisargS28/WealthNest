import os
import logging
import psycopg2
import calendar
import hashlib
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.api.auth import get_auth_token

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)


def compute_next_expected(sip_day: int) -> date:
    """Returns the next calendar date on which the SIP day falls."""
    today = date.today()
    if today.day <= sip_day:
        try:
            return today.replace(day=sip_day)
        except ValueError:
            last_day = calendar.monthrange(today.year, today.month)[1]
            return today.replace(day=last_day)
    else:
        if today.month == 12:
            y, m = today.year + 1, 1
        else:
            y, m = today.year, today.month + 1
        try:
            return date(y, m, sip_day)
        except ValueError:
            last_day = calendar.monthrange(y, m)[1]
            return date(y, m, last_day)


class SIPPlanUpdateRequest(BaseModel):
    sip_day: Optional[int] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None
    status: Optional[str] = None


class ConfirmOccurrenceRequest(BaseModel):
    actual_date: Optional[str] = None    # YYYY-MM-DD; defaults to expected_date
    actual_amount: Optional[float] = None  # defaults to plan amount


@router.get("/sip-plans")
def get_sip_plans(token: Optional[str] = Depends(get_auth_token)):
    """Returns all SIP plans for the user's portfolios."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT sp.id, sp.portfolio_id, sp.folio_id, sp.scheme_id,
                   sp.amount, sp.frequency, sp.sip_day, sp.start_date,
                   sp.next_expected_date, sp.status, sp.created_at,
                   s.scheme_name, f.folio_number
            FROM public.sip_plans sp
            JOIN public.schemes s ON sp.scheme_id = s.id
            JOIN public.folios f ON sp.folio_id = f.id
            ORDER BY sp.created_at DESC
        """)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        plans = []
        for row in rows:
            obj = dict(zip(cols, row))
            for k, v in obj.items():
                if hasattr(v, 'isoformat'):
                    obj[k] = v.isoformat()
                elif hasattr(v, '__float__') and type(v).__name__ == 'Decimal':
                    obj[k] = float(v)
            plans.append(obj)
        return {"sip_plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.patch("/sip-plans/{sip_plan_id}")
def update_sip_plan(sip_plan_id: str, body: SIPPlanUpdateRequest, token: Optional[str] = Depends(get_auth_token)):
    """Update a SIP plan's day, amount, frequency, or status. Recalculates next_expected_date."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch current plan
        cursor.execute("SELECT sip_day, status FROM public.sip_plans WHERE id = %s", (sip_plan_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="SIP plan not found")

        current_day, current_status = row

        updates = []
        params = []

        if body.sip_day is not None:
            if not (1 <= body.sip_day <= 31):
                raise HTTPException(status_code=400, detail="sip_day must be between 1 and 31")
            updates.append("sip_day = %s")
            params.append(body.sip_day)
            next_date = compute_next_expected(body.sip_day)
            updates.append("next_expected_date = %s")
            params.append(next_date)

        if body.amount is not None:
            updates.append("amount = %s")
            params.append(Decimal(str(body.amount)))

        if body.frequency is not None:
            updates.append("frequency = %s")
            params.append(body.frequency)

        if body.status is not None:
            updates.append("status = %s")
            params.append(body.status)

        if not updates:
            return {"success": True, "message": "No changes"}

        updates.append("updated_at = NOW()")
        params.append(sip_plan_id)

        cursor.execute(
            f"UPDATE public.sip_plans SET {', '.join(updates)} WHERE id = %s",
            params
        )
        conn.commit()
        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("/sip-occurrences/{occurrence_id}/confirm")
def confirm_sip_occurrence(
    occurrence_id: str,
    body: ConfirmOccurrenceRequest,
    token: Optional[str] = Depends(get_auth_token)
):
    """
    User confirms that a SIP debit went through.
    Creates a real transaction in the transactions table and marks the occurrence as CONFIRMED.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch the occurrence + plan details
        cursor.execute("""
            SELECT so.id, so.sip_plan_id, so.expected_date, so.amount, so.status,
                   sp.folio_id, sp.scheme_id, sp.sip_day
            FROM public.sip_occurrences so
            JOIN public.sip_plans sp ON so.sip_plan_id = sp.id
            WHERE so.id = %s
        """, (occurrence_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="SIP occurrence not found")

        (occ_id, plan_id, expected_date, plan_amount, occ_status,
         folio_id, scheme_id, sip_day) = row

        if occ_status == "CONFIRMED":
            return {"success": True, "message": "Already confirmed"}

        actual_date = date.fromisoformat(body.actual_date) if body.actual_date else expected_date
        actual_amount = Decimal(str(body.actual_amount)) if body.actual_amount else plan_amount

        # Create the transaction
        desc = f"SIP Confirmation - {actual_date.strftime('%d-%b-%Y')}"
        fingerprint_raw = f"{folio_id}|{scheme_id}|{actual_date.isoformat()}|{desc}|{actual_amount}"
        fingerprint = hashlib.sha256(fingerprint_raw.encode()).hexdigest()

        # Check duplicate
        cursor.execute("SELECT id FROM public.transactions WHERE fingerprint = %s", (fingerprint,))
        existing_tx = cursor.fetchone()

        tx_id = None
        if not existing_tx:
            cursor.execute("""
                INSERT INTO public.transactions
                    (folio_id, scheme_id, transaction_date, transaction_type, description,
                     amount, source_type, fingerprint)
                VALUES (%s, %s, %s, 'PURCHASE', %s, %s, 'MANUAL_SIP_CONFIRM', %s)
                RETURNING id
            """, (folio_id, scheme_id, actual_date, desc, actual_amount, fingerprint))
            tx_id = cursor.fetchone()[0]

        # Mark occurrence as CONFIRMED
        cursor.execute("""
            UPDATE public.sip_occurrences
            SET status = 'CONFIRMED',
                actual_date = %s,
                amount = %s,
                transaction_id = %s,
                confirmed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (actual_date, actual_amount, tx_id, occurrence_id))

        # Mark related notifications as read
        cursor.execute("""
            UPDATE public.notifications
            SET status = 'READ', read_at = NOW()
            WHERE entity_type = 'sip_occurrence' AND entity_id = %s
        """, (occurrence_id,))

        conn.commit()

        # Recalculate portfolio valuation
        try:
            cursor.execute("""
                SELECT a.portfolio_id FROM folios f
                JOIN assets a ON f.asset_id = a.id
                WHERE f.id = %s
            """, (folio_id,))
            port_row = cursor.fetchone()
            if port_row:
                from app.services.valuation_service import ValuationService
                ValuationService().refresh_valuation(str(port_row[0]))
        except Exception as val_ex:
            logger.warning(f"Valuation refresh after SIP confirm failed: {val_ex}")

        return {"success": True, "transaction_id": str(tx_id) if tx_id else None}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
