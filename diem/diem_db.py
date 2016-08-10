import sqlite3


def open_db(db_name):
    return sqlite3.connect(db_name)


def create_tables(conn):
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS diem_date_index (
          tid             INTEGER PRIMARY KEY,
          diary_date      DATE
        )
        ''',

        '''
        CREATE TABLE IF NOT EXISTS diem_id_index (
          mid             INTEGER PRIMARY KEY,
          tid             INTEGER
        )
        ''',

        '''
        CREATE INDEX IF NOT EXISTS tid_index ON diem_id_index(tid)
        '''
    ]

    c = conn.cursor()
    for query in queries:
        c.execute(query)

    conn.commit()

    return conn


def get_latest_tid(conn):
    query = '''SELECT MAX(tid) FROM diem_date_index'''

    c = conn.cursor()
    c.execute(query)

    tid = c.fetchone()[0]
    if tid is None:
        return 0

    return tid


def update_date_index(conn, dates):
    date_items = [(tid, date) for tid, date in dates.items()]

    c = conn.cursor()
    c.executemany('INSERT OR REPLACE INTO diem_date_index (tid, diary_date) VALUES (?, ?)', date_items)
    conn.commit()


def update_id_index(conn, structure):
    mid_tid_items = [(mid, tid) for mid, tid in structure if mid != tid]

    c = conn.cursor()
    c.executemany('INSERT OR REPLACE INTO diem_id_index (mid, tid) VALUES (?, ?)', mid_tid_items)
    conn.commit()
