#!/usr/bin/env python3

from argparse import ArgumentParser
from sys import stdout

import logging

from diem import diem_db

logger = logging.getLogger(__name__)


def init_parser():

    parser = ArgumentParser()

    parser.add_argument('-c', '--credential', default='credential.json',
                        help='Credential file path. Defaults to credential.json.')

    parser.add_argument('-d', '--database', default='diem.db', help='Database path. Defaults to diem.db.')

    parser.add_argument('-e', '--email', help='Your email address.')

    parser.add_argument('-f', '--log-file', default='lifemotif-diem.log',
                        help='Log file path. Defaults to lifemotif-diem.log.')

    parser.add_argument('-k', '--label-id', help='Your target email label.')

    parser.add_argument('-l', '--log-level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', ],
                        default='INFO',
                        help='Log level. Defaults to INFO.')

    parser.add_argument('-s', '--storage', default='storage.json',
                        help='OAUTH2 storage path. Defaults to storage.json')

    parser.add_argument('--authorize', action='store_true', help='Authorization mode.')

    parser.add_argument('--create-tables', action='store_true', help='Creating table mode. Create database tables.')

    parser.add_argument('--fetch', action='store_true', help='Fetch mode. Store your emails locally.')

    parser.add_argument('--list-label', action='store_true', help='Label listing mode. List your email labels.')

    parser.add_argument('--dest-dir', default='archive',
                        help='MIME Message output path. Defaults to archive. Only applied to fetch mode.')

    parser.add_argument('--latest-tid', type=str, default='latest',
                        help='Number of latest thread id. Only applied when you fetch. '
                             'Set 0 to fetch unlimited number of emails, '
                             'or input hexadecimal value to fetch emails whose id is greater than the value.')

    return parser.parse_args()


def init_logger(log_level, log_stream):

    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level %s' % log_level)

    log_format = '%(asctime)s [%(levelname)s] %(name)s (%(lineno)s): %(message)s'
    logging.basicConfig(format=log_format, stream=log_stream, level=numeric_level)


def init_cli():
    init_cli.args = init_parser()
    init_cli.conn = diem_db.open_db(init_cli.args.database)

    if init_cli.args.log_file == '-':
        init_cli.log_stream = stdout
    else:
        init_cli.log_stream = open(init_cli.args.log_file, 'a')

    init_logger(log_level=init_cli.args.log_level, log_stream=init_cli.log_stream)


init_cli.args = None
init_cli.conn = None


def deinit_cli():
    if not init_cli.conn:
        init_cli.conn.close()
        init_cli.conn = None


def do_cli_job():

    conn = init_cli.conn
    args = init_cli.args

    # creating tables
    if args.create_tables:
        logger.debug('creating tables. db name=%s' % init_cli.args.database)
        diem_db.create_tables(conn)
        logger.info('Tables are created successfully.')
        return

    # authorization process
    # required:
    #   credential file path
    #   storage file path
    if args.authorize:
        from diem.gmail_api import authorize

        authorize(credential_file=args.credential, storage_file=args.storage)
        logger.info('Authorization process complete.')
        return

    # label listing process
    # required:
    #   storage file path (you must be authorized)
    #   email address
    if args.list_label:
        from diem.gmail_api import get_service, get_labels

        if not args.email:
            error_email_address_required()
            return

        labels = get_labels(service=get_service(args.storage), email=args.email)
        for label in labels:
            print('%s %s' % (label['id'], label['name']))
        return

    # email fetching process
    # required:
    #   storage file path (you must be authorized)
    #   email address
    #   label id
    #   output path
    if args.fetch:
        from diem.diem_db import get_latest_tid, update_date_index, update_id_index
        from diem.gmail_api import get_service
        from diem.gmail_fetch import fetch_structure, fetch_diary_dates, fetch_reply_mails

        # argument checking
        if not args.email:
            error_email_address_required()
            return
        if not args.label_id:
            error_label_id_required()
            return

        # service
        service = get_service(args.storage)

        # fetch email structure from latest tid
        # latest tid is given from database or command line option.
        structure = fetch_structure(
            service=service,
            email=args.email,
            label_id=args.label_id,
            latest_tid=get_latest_tid(conn) if args.latest_tid == 'latest' else int(args.latest_tid, 16)
        )

        # update id index.
        # with id index, we can identify which message id / thread id pair
        update_id_index(conn, structure)

        # fetch diary date from alarm mails ...
        dates = fetch_diary_dates(service, args.email, structure)
        # and store into database
        update_date_index(conn, dates)

        # fetch reply mails
        fetch_reply_mails(service, args.email, structure, args.dest_dir)

        logger.info('Fetching complete.')
        return


def error_email_address_required():
    from sys import stderr
    print('Email address is required. Please input your email with -e/--email option.', file=stderr)


def error_label_id_required():
    from sys import stderr
    print('Label ID is required. Please input desired email label id with -k/--label-id option.', file=stderr)

if __name__ == '__main__':
    init_cli()
    do_cli_job()
    deinit_cli()
