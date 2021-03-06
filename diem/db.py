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

    return execute_and_commit(conn, queries)


def drop_tables(conn):
    queries = [
        'DROP TABLE diem_date_index',
        'DROP TABLE diem_id_index',
    ]

    return execute_and_commit(conn, queries)


def execute_and_commit(conn, queries):
    c = conn.cursor()
    for query in queries:
        c.execute(query)

    conn.commit()

    return conn


def get_latest_mid(conn):
    query = '''SELECT MAX(mid) FROM diem_id_index'''

    c = conn.cursor()
    c.execute(query)

    mid = c.fetchone()[0]
    if mid is None:
        return 0

    return mid


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


def is_valid_mid(conn, mid):
    return conn.execute('SELECT COUNT(*) FROM diem_id_index WHERE mid=?', (mid, )).fetchone()[0]


def get_diary_date(conn, mid):
    query = '''
            SELECT date_index.diary_date FROM diem_date_index AS date_index
              JOIN diem_id_index AS id_index ON date_index.tid = id_index.tid
            WHERE id_index.mid = ?
            '''

    result = conn.execute(query, (mid, )).fetchone()

    if result:
        return result[0]

