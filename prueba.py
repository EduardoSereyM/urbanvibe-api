import psycopg2, os
dsn = "postgresql://postgres.wujebyuplaghuiaadejm:TU_PASSWORD@aws-1-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require"
with psycopg2.connect(dsn) as con:
    with con.cursor() as cur:
        cur.execute("select 1;")
        print(cur.fetchone())
