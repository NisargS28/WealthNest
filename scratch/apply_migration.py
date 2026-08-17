import os
import psycopg2

db_url = os.environ.get("Database_URL", "postgresql://postgres.ffkaicjknhirjkahjcwf:Nisarg%402888@aws-0-ap-south-1.pooler.supabase.com:5432/postgres")

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE public.portfolio_valuations 
        ADD COLUMN IF NOT EXISTS one_day_change NUMERIC,
        ADD COLUMN IF NOT EXISTS one_day_change_percent NUMERIC;
    """)
    conn.commit()
    print("Migration applied successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
