import os
import logging
import psycopg2
import calendar
from decimal import Decimal
from datetime import date

logger = logging.getLogger(__name__)


def get_db_connection():
    db_url = os.environ.get("Database_URL")
    if not db_url:
        db_url = "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"
    return psycopg2.connect(db_url)


def compute_next_expected(sip_day: int, from_date: date) -> date:
    """Returns the next occurrence of sip_day on or after from_date + 1 month."""
    if from_date.month == 12:
        y, m = from_date.year + 1, 1
    else:
        y, m = from_date.year, from_date.month + 1
    try:
        return date(y, m, sip_day)
    except ValueError:
        last_day = calendar.monthrange(y, m)[1]
        return date(y, m, last_day)


def check_and_create_sip_occurrences():
    """
    Daily job: For every ACTIVE/PENDING_CONFIRMATION sip_plan whose next_expected_date
    is on or before today, create a sip_occurrences record and a SIP_CONFIRMATION
    notification so the user can confirm the actual transaction.

    Also handles missed/past-due occurrences that were never recorded.
    """
    logger.info("[SIP Reminder] Checking for due SIP occurrences...")
    today = date.today()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch all active SIP plans that are due
        cursor.execute("""
            SELECT sp.id, sp.sip_day, sp.amount, sp.next_expected_date,
                   sp.folio_id, sp.scheme_id, sp.portfolio_id, sp.status,
                   s.scheme_name, p.owner_user_id
            FROM public.sip_plans sp
            JOIN public.schemes s ON sp.scheme_id = s.id
            JOIN public.portfolios p ON sp.portfolio_id = p.id
            WHERE sp.status IN ('ACTIVE', 'PENDING_CONFIRMATION')
              AND sp.next_expected_date <= %s
        """, (today,))
        due_plans = cursor.fetchall()

        created = 0
        for row in due_plans:
            (plan_id, sip_day, amount, expected_date,
             folio_id, scheme_id, portfolio_id, status,
             scheme_name, user_id) = row

            if not user_id:
                continue

            # Check if an occurrence already exists for this expected_date
            cursor.execute("""
                SELECT id FROM public.sip_occurrences
                WHERE sip_plan_id = %s AND expected_date = %s
            """, (plan_id, expected_date))
            if cursor.fetchone():
                # Already has an occurrence — just advance next_expected_date
                next_date = compute_next_expected(sip_day, expected_date)
                cursor.execute(
                    "UPDATE public.sip_plans SET next_expected_date = %s, updated_at = NOW() WHERE id = %s",
                    (next_date, plan_id)
                )
                conn.commit()
                continue

            # Create a sip_occurrence
            cursor.execute("""
                INSERT INTO public.sip_occurrences
                    (sip_plan_id, expected_date, amount, status)
                VALUES (%s, %s, %s, 'PENDING')
                RETURNING id
            """, (plan_id, expected_date, amount))
            occurrence_id = cursor.fetchone()[0]

            # Create a SIP_CONFIRMATION notification
            cursor.execute("""
                INSERT INTO public.notifications
                    (user_id, type, title, message, entity_type, entity_id, status)
                VALUES (%s, 'SIP_CONFIRMATION', %s, %s, 'sip_occurrence', %s, 'UNREAD')
            """, (
                user_id,
                f"SIP Due: {scheme_name}",
                f"\u20b9{amount:,.0f} SIP was expected on {expected_date.strftime('%d %b %Y')}. Did it go through? Please confirm.",
                occurrence_id
            ))

            # Advance next_expected_date on the plan
            next_date = compute_next_expected(sip_day, expected_date)
            cursor.execute(
                "UPDATE public.sip_plans SET next_expected_date = %s, updated_at = NOW() WHERE id = %s",
                (next_date, plan_id)
            )
            conn.commit()
            created += 1
            logger.info(
                f"[SIP Reminder] Created occurrence for '{scheme_name}' on {expected_date} "
                f"(next: {next_date})"
            )

        logger.info(f"[SIP Reminder] Done. Created {created} new occurrence(s).")

    except Exception as e:
        logger.error(f"[SIP Reminder] Failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
