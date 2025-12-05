import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname="restaurant_db",
        user="postgres",
        password="user@123",
        host="localhost",
        port=5434,
    )

def advance_orders():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE orders
            SET status = CASE status
                WHEN 'PENDING'    THEN 'CONFIRMED'
                WHEN 'CONFIRMED'  THEN 'IN_KITCHEN'
                WHEN 'IN_KITCHEN' THEN 'READY'
                WHEN 'READY'      THEN 'COMPLETED'
                ELSE status
            END,
            updated_at = NOW()
            WHERE status IN ('PENDING', 'CONFIRMED', 'IN_KITCHEN', 'READY');
        """)
        conn.commit()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    advance_orders()
