import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'realestate_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Ktvab@2k')
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_all_properties():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.property_id, p.address, p.metro_area, p.sq_footage, p.property_type,
               f.revenue, f.net_income, f.expenses
        FROM properties p
        JOIN financials f ON p.property_id = f.property_id
        ORDER BY p.property_id
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_properties_by_metro(metro_area):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.property_id, p.address, p.metro_area, p.sq_footage, p.property_type,
               f.revenue, f.net_income, f.expenses
        FROM properties p
        JOIN financials f ON p.property_id = f.property_id
        WHERE LOWER(p.metro_area) LIKE LOWER(%s)
        ORDER BY f.revenue DESC
    ''', (f'%{metro_area}%',))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_properties_by_type(property_type):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.property_id, p.address, p.metro_area, p.sq_footage, p.property_type,
               f.revenue, f.net_income, f.expenses
        FROM properties p
        JOIN financials f ON p.property_id = f.property_id
        WHERE LOWER(p.property_type) LIKE LOWER(%s)
        ORDER BY f.revenue DESC
    ''', (f'%{property_type}%',))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_top_revenue_properties(limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.property_id, p.address, p.metro_area, p.sq_footage, p.property_type,
               f.revenue, f.net_income, f.expenses
        FROM properties p
        JOIN financials f ON p.property_id = f.property_id
        ORDER BY f.revenue DESC
        LIMIT %s
    ''', (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_total_financials():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT SUM(revenue), SUM(net_income), SUM(expenses)
        FROM financials
    ''')
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def get_financials_by_metro():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.metro_area,
               SUM(f.revenue) as total_revenue,
               SUM(f.net_income) as total_net_income,
               SUM(f.expenses) as total_expenses,
               COUNT(*) as property_count
        FROM properties p
        JOIN financials f ON p.property_id = f.property_id
        GROUP BY p.metro_area
        ORDER BY total_revenue DESC
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
