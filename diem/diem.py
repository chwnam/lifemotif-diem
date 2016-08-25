from logging import getLogger
from os.path import join as path_join
from os.path import exists as path_exists

from . import db as diem_db
from gmail.api import get_service
from gmail import fetch as gmail_fetch

logger = getLogger(__name__)


def authorize(credential, storage):
    from gmail.api import authorize
    authorize(credential_file=credential, storage_file=storage)
    logger.info('Authorization process complete.')


def get_labels(storage, email):
    from gmail.api import get_service, get_labels
    labels = get_labels(service=get_service(storage), email=email)
    return labels


def create_tables(conn):
    diem_db.create_tables(conn)
    logger.info('create_tables completed.')


def drop_tables(conn):
    diem_db.drop_tables(conn)
    logger.info('drop_tables completed.')


def update_database(conn, storage, email, label_id):

    logger.info('update_database started.')

    service = get_service(storage)

    # fetch structure: list of (mid, tid)
    structure = gmail_fetch.fetch_structure(
        service=service,
        email=email,
        label_id=label_id,
        latest_mid=diem_db.get_latest_mid(conn)
    )

    diem_db.update_id_index(conn, structure)

    # extract all diary date within alarm mails: dict mid --> date
    date_indices = gmail_fetch.extract_diary_dates(
        service=service,
        email=email,
        structure=structure
    )

    diem_db.update_date_index(conn, date_indices)

    logger.info('update_database completed.')

    return structure, date_indices


def rebuild_database(conn, storage, email, label_id):
    logger.info('rebuild_database started.')
    drop_tables(conn)
    create_tables(conn)
    update_database(conn, storage, email, label_id)
    logger.info('rebuild_database completed.')


def query(conn, query_string):
    raise Exception('Not implemented yet!')


def fetch(storage, email, archive_path, mid_list):
    service = get_service(storage)
    gmail_fetch.fetch_and_archive(service, email, archive_path, mid_list)


def fetch_incrementally(conn, storage, email, label_id, archive_path):
    logger.info('fetch_incrementally started.')

    structure, date_indices = update_database(conn, storage, email, label_id)

    mid_list = [mid for mid, tid in structure if mid != tid]
    if mid_list:
        service = get_service(storage)
        gmail_fetch.fetch_and_archive(service, email, archive_path, mid_list)

    logger.info('fetch_incrementally completed.')


def fix_missing(conn, storage, email, archive_path):
    logger.info('fix_missing started.')

    q = "SELECT mid FROM diem_id_index WHERE mid != tid ORDER BY mid DESC"
    mid_list = []

    for row in conn.execute(q):

        mid = row[0]

        message_path = path_join(archive_path, '%x.gz' % mid)
        if path_exists(message_path):
            logger.debug('mid %d (0x%x) already archived.' % (mid, mid))
        else:
            logger.debug('mid %d (0x%x) not archived. Append to mid_list' % (mid, mid))
            mid_list.append(mid)

    fetch(storage, email, archive_path, mid_list)

    logger.info('fix_missing_completed. %d message(s) archived.')

