from argparse import ArgumentParser
from sys import exit, stdout
from os.path import expanduser

import logging
import logging.config

from diem import diem_db

logger = logging.getLogger(__name__)


class DiemLogging(object):
    log_format = '%(asctime)s [%(levelname)s] %(name)s (%(lineno)s): %(message)s'

    log_config = {
        'version': 1,
        'formatters': {
            'verbose': {
                'format': log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': '%(levelname)-8s %(message)s',
            }
        },
        'filters': {
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'level': 'INFO',
                'filters': [],
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': None,  # Set this!
                'formatter': 'verbose',
                'filters': [],
                'level': 'DEBUG',
                'maxBytes': 20 * 1024,  # 20KiB
                'backupCount': 10,       #
                'encoding': 'utf-8',
            },
            'null': {
                'class': 'logging.NullHandler',
                'level': 'DEBUG',
            }
        },
        'loggers': {
            '__main__': {
                'handlers': ['console', 'file'],
                'propagate': True,
                'level': 'DEBUG',
            },
            'diem': {
                'handlers': ['console', 'file'],
                'propagate': True,
                'level': 'DEBUG',
            },
            'googleapiclient': {
                'handlers': ['null'],
                'propagate': False,
                'level': 'DEBUG',
            }
        }
    }

    @staticmethod
    def get_log_level_value(log_level):
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level %s' % log_level)

        return numeric_level

    @staticmethod
    def get_log_stream(log_file):
        if log_file == '-':
            log_stream = stdout
        else:
            log_stream = open(log_file, 'a')

        return log_stream

    @classmethod
    def set_basic_config(cls, log_level, log_file):
        log_stream = cls.get_log_level_value(log_file)
        numeric_level = cls.get_log_level_value(log_level)
        logging.basicConfig(format=cls.log_format, stream=log_stream, level=numeric_level)

    @classmethod
    def set_dict_config(cls, log_level, log_file):
        cls.log_config['handlers']['file']['level'] = log_level
        cls.log_config['handlers']['file']['filename'] = log_file
        logging.config.dictConfig(cls.log_config)


class DiemArguments(object):
    @staticmethod
    def get_arguments():
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

        parser.add_argument('-v', '--version', action='store_true',
                            help='Show program version.')

        parsed = parser.parse_args()

        for attr in ['credential', 'storage', 'database', 'dest_dir', 'log_file']:
            if not hasattr(parsed, attr):
                continue
            val = getattr(parsed, attr)
            if '~' in val:
                setattr(parsed, attr, expanduser(val))

        return parsed


class Diem(object):
    version = '1.0.2'

    def __init__(self):
        self.conn = None
        self.arguments = None

    def __del__(self):
        self.conn_close()

    def conn_close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        """
        DB table creation
        """
        diem_db.create_tables(self.conn)
        logger.info('Tables are created successfully.')

    @staticmethod
    def authorize(credential, storage):
        """
        Authorization process
        Required:
            credential file path
            storage file path
        """
        from diem.gmail_api import authorize
        authorize(credential_file=credential, storage_file=storage)
        logger.info('Authorization process complete.')

    @staticmethod
    def get_labels(storage, email):
        """
        Label listing process
        Required:
           storage file path (you must be authorized)
           email address
        """
        from diem.gmail_api import get_service, get_labels
        labels = get_labels(service=get_service(storage), email=email)
        return labels

    def fetch(self, storage, email, label_id, latest_tid, dest_dir):
        """
        Email fetching process
        Required:
           storage file path (you must be authorized)
           email address
           label id
           output path
        """
        from diem.diem_db import get_latest_tid, update_date_index, update_id_index
        from diem.gmail_api import get_service
        from diem.gmail_fetch import fetch_structure, fetch_diary_dates, fetch_reply_mails

        # service
        service = get_service(storage)

        if latest_tid == 'latest':
            _latest_tid = get_latest_tid(self.conn)
        else:
            _latest_tid = int(latest_tid, 16)

        # update email structure from latest tid
        structure = fetch_structure(
            service=service,
            email=email,
            label_id=label_id,
            latest_tid=_latest_tid
        )

        # update id index.
        # with id index, we can identify message id / thread id groups
        update_id_index(self.conn, structure)

        # fetch diary date from alarm mails ...
        dates = fetch_diary_dates(service, email, structure)

        # and store into database
        update_date_index(self.conn, dates)

        # fetch reply mails
        fetch_reply_mails(service, email, structure, dest_dir)

        logger.info('Fetching complete.')

    @staticmethod
    def error_email_address_required():
        from sys import stderr
        print('Email address is required. Please input your email with -e/--email option.', file=stderr)

    @staticmethod
    def error_label_id_required():
        from sys import stderr
        print('Label ID is required. Please input desired email label id with -k/--label-id option.', file=stderr)

    def run_cli(self):
        self.conn_close()
        self.arguments = DiemArguments.get_arguments()
        self.conn = diem_db.open_db(self.arguments.database)

        DiemLogging.set_dict_config(self.arguments.log_level, self.arguments.log_file)

        if self.version:
            print(self.version)
            return

        if self.arguments.create_tables:
            self.create_tables()
            return

        if self.arguments.authorize:
            self.authorize(self.arguments.credential, self.arguments.storage)
            return

        if self.arguments.list_label:
            # argument checking
            if not self.arguments.email:
                self.error_email_address_required()
                exit(1)

            labels = self.get_labels(self.arguments.storage, self.arguments.email)

            for label in labels:
                print('%s %s' % (label['id'], label['name']))
            return

        if self.arguments.fetch:
            # argument checking
            if not self.arguments.email:
                self.error_email_address_required()
                exit(1)
            if not self.arguments.label_id:
                self.error_label_id_required()
                exit(1)

            self.fetch(
                self.arguments.storage,
                self.arguments.email,
                self.arguments.label_id,
                self.arguments.latest_tid,
                self.arguments.dest_dir
            )
            return