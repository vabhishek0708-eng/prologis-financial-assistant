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

PROPERTIES = [
    (1, '233 S Wacker Dr', 'Chicago', 1850000, 'Office'),
    (2, '350 N Orleans St', 'Chicago', 420000, 'Industrial'),
    (3, '1 Infinite Loop', 'San Francisco', 980000, 'Office'),
    (4, '2000 W Fulton St', 'Chicago', 310000, 'Industrial'),
    (5, '555 Market St', 'San Francisco', 670000, 'Retail'),
    (6, '100 Main St', 'Dallas', 540000, 'Mixed-Use'),
    (7, '400 Commerce St', 'Dallas', 280000, 'Industrial'),
    (8, '1200 Brickell Ave', 'Miami', 760000, 'Office'),
    (9, '88 NW 7th St', 'Miami', 190000, 'Retail'),
    (10, '5000 Forbes Ave', 'Pittsburgh', 430000, 'Office'),
    (11, '300 W Adams St', 'Chicago', 510000, 'Office'),
    (12, '1401 S Michigan Ave', 'Chicago', 240000, 'Retail'),
    (13, '900 Market St', 'San Francisco', 380000, 'Retail'),
    (14, '2500 Ross Ave', 'Dallas', 620000, 'Office'),
    (15, '3100 McKinnon St', 'Dallas', 350000, 'Mixed-Use'),
    (16, '200 SE 1st St', 'Miami', 290000, 'Industrial'),
    (17, '777 Brickell Ave', 'Miami', 840000, 'Office'),
    (18, '1 PPG Place', 'Pittsburgh', 570000, 'Office'),
    (19, '4400 Fifth Ave', 'Pittsburgh', 210000, 'Retail'),
    (20, '600 W Chicago Ave', 'Chicago', 730000, 'Mixed-Use'),
    (21, '150 California St', 'San Francisco', 490000, 'Office'),
    (22, '3000 Stemmons Fwy', 'Dallas', 460000, 'Industrial'),
]

FINANCIALS = [
    (1, 14200000, 4100000, 8900000),
    (2, 3800000, 920000, 2100000),
    (3, 11500000, 3400000, 7200000),
    (4, 2900000, 680000, 1700000),
    (5, 6200000, 1800000, 3900000),
    (6, 5100000, 1400000, 3100000),
    (7, 2600000, 590000, 1500000),
    (8, 8900000, 2600000, 5500000),
    (9, 1700000, 410000, 980000),
    (10, 4800000, 1300000, 2900000),
    (11, 6100000, 1750000, 3800000),
    (12, 2200000, 520000, 1300000),
    (13, 4100000, 1100000, 2500000),
    (14, 7200000, 2100000, 4400000),
    (15, 3900000, 1050000, 2300000),
    (16, 2400000, 550000, 1400000),
    (17, 9800000, 2900000, 6100000),
    (18, 6400000, 1850000, 3900000),
    (19, 1900000, 450000, 1100000),
    (20, 8100000, 2350000, 5000000),
    (21, 5600000, 1600000, 3400000),
    (22, 3500000, 820000, 2100000),
]

def seed_database():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                property_id SERIAL PRIMARY KEY,
                address VARCHAR(255) NOT NULL,
                metro_area VARCHAR(100) NOT NULL,
                sq_footage INTEGER NOT NULL,
                property_type VARCHAR(50) NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS financials (
                id SERIAL PRIMARY KEY,
                property_id INTEGER REFERENCES properties(property_id),
                revenue BIGINT NOT NULL,
                net_income BIGINT NOT NULL,
                expenses BIGINT NOT NULL
            )
        ''')
        cur.execute('DELETE FROM financials')
        cur.execute('DELETE FROM properties')
        cur.executemany('INSERT INTO properties (property_id, address, metro_area, sq_footage, property_type) VALUES (%s, %s, %s, %s, %s)', PROPERTIES)
        cur.executemany('INSERT INTO financials (property_id, revenue, net_income, expenses) VALUES (%s, %s, %s, %s)', FINANCIALS)
        conn.commit()
        cur.close()
        conn.close()
        print('Database seeded successfully with ' + str(len(PROPERTIES)) + ' properties and ' + str(len(FINANCIALS)) + ' financial records')
    except Exception as e:
        print('Database error: ' + str(e))

if __name__ == '__main__':
    seed_database()
