from argparse import ArgumentParser
from os.path import expanduser

from . import DIEM_VERSION

from re import compile, IGNORECASE


def get_args():
    parser = build_parser()
    args = parser.parse_args()

    # expand ~ as home directory
    filter_arg_values(
        args=args,
        attributes=['credential', 'storage', 'database', 'dest_dir', 'log_file'],
        decision_func=lambda v: len(v) > 1 and v[0] == '~',
        filter_func=expanduser
    )

    mid_expr = compile(r'^0x([0-9a-f]{16})$', IGNORECASE)

    # convert hexadecimal strings into decimal strings
    filter_arg_values(
        args=args,
        attributes=['query_string', 'mid'],
        decision_func=lambda v: mid_expr.match(v),
        filter_func=lambda v: int(v, 16)
    )

    # convert numerical date into int type
    filter_arg_values(
        args=args,
        attributes=['query_string', 'mid'],
        decision_func=lambda v: v.isdigit(),
        filter_func=lambda v: int(v)
    )

    return args


def build_parser():
    parser = ArgumentParser()

    add_common_arguments(parser)

    subparsers = parser.add_subparsers(dest='subcommand')

    add_authorize_parser(subparsers)
    add_list_label_parser(subparsers)

    add_create_tables_parser(subparsers)
    add_drop_tables_parser(subparsers)

    add_update_database_parser(subparsers)
    add_rebuild_database_parser(subparsers)

    add_query_parser(subparsers)

    add_fetch_parser(subparsers)
    add_fetch_incrementally_parser(subparsers)

    add_fix_missing_parser(subparsers)

    add_export_parser(subparsers)

    return parser


def filter_arg_values(args, attributes, decision_func, filter_func):
    for attr in attributes:
        if hasattr(args, attr):
            val = getattr(args, attr)
            if type(val) == str:
                if decision_func(val):
                    setattr(args, attr, filter_func(val))
            elif type(val) == list:
                r = [filter_func(x) if decision_func(x) else x for x in val]
                setattr(args, attr, r)


# sub parsers below ##############################################################################################
def add_authorize_parser(subparsers):
    p = subparsers.add_parser('authorize', aliases=['a'], help='OAUTH2 authorization')

    add_credential_argument(p)
    add_storage_argument(p)


def add_list_label_parser(subparsers):
    p = subparsers.add_parser('list-label', aliases=['ll'])

    add_storage_argument(p)
    add_email_argument(p)


def add_create_tables_parser(subparsers):
    p = subparsers.add_parser('create-tables', aliases=['ct'])

    add_db_argument(p)


def add_drop_tables_parser(subparsers):
    p = subparsers.add_parser('drop-tables', aliases=['dt'])

    add_db_argument(p)
    add_force_argument(p)


def add_update_database_parser(subparsers):
    p = subparsers.add_parser('update-database', aliases=['ud'])

    add_db_argument(p)
    add_storage_argument(p)
    add_email_argument(p)
    add_label_id_argument(p)


def add_rebuild_database_parser(subparsers):
    p = subparsers.add_parser('rebuild-database', aliases=['rd'])

    add_db_argument(p)
    add_storage_argument(p)
    add_email_argument(p)
    add_label_id_argument(p)
    add_force_argument(p)


def add_query_parser(subparsers):
    p = subparsers.add_parser('query', aliases=['q'])

    add_db_argument(p)
    add_query_string_argument(p)


def add_fetch_parser(subparsers):
    p = subparsers.add_parser('fetch', aliases=['f'])

    add_storage_argument(p)
    add_email_argument(p)
    add_archive_path_argument(p)
    add_mid_argument(p, required=True, nargs='+')


def add_fetch_incrementally_parser(subparsers):
    p = subparsers.add_parser('fetch-incrementally', aliases=['fi'])

    add_db_argument(p)
    add_storage_argument(p)
    add_email_argument(p)
    add_label_id_argument(p)
    add_archive_path_argument(p)


def add_fix_missing_parser(subparsers):
    p = subparsers.add_parser('fix-missing', aliases=['fm'])

    add_db_argument(p)
    add_storage_argument(p)
    add_email_argument(p)
    add_archive_path_argument(p)


def add_export_parser(subparsers):
    p = subparsers.add_parser('export', aliases=['e'])

    add_db_argument(p)
    add_mid_argument(p, required=True)
    add_archive_path_argument(p)

    p.add_argument('--list-converters', action='store_true')

# end of subparsers ##############################################################################################


# arguments below ################################################################################################
def add_credential_argument(parser, **kwargs):
    parser.add_argument('-c', '--credential', default='credential.json',
                        help='Credential file path. Defaults to credential.json.',
                        **kwargs)


def add_storage_argument(parser, **kwargs):
    parser.add_argument('-s', '--storage', default='storage.json',
                        help='OAUTH2 storage file path. '
                             'Tokens are saved in this file. Defaults to storage.json.',
                        **kwargs)


def add_email_argument(parser, **kwargs):
    parser.add_argument('-e', '--email', required=True,
                        help='Your email address.',
                        **kwargs)


def add_label_id_argument(parser, **kwargs):
    parser.add_argument('-k', '--label-id', required=True,
                        help='Your target email label ID.',
                        **kwargs)


def add_db_argument(parser, **kwargs):
    parser.add_argument('-d', '--database', default='diem.db',
                        help='Database path. Defaults to diem.db.',
                        **kwargs)


def add_force_argument(parser, **kwargs):
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Do not ask when prompting.',
                        **kwargs)


def add_archive_path_argument(parser, **kwargs):
    parser.add_argument('-o', '--archive-path', default='archives',
                        help='MIME Message output path. Defaults to archives.',
                        **kwargs)


def add_query_string_argument(parser, **kwargs):
    parser.add_argument('-i', '--string', required=True, dest='query_string',
                        help='Query string. '
                             'It can be an integer, a hexadecimal, or a date string in yyyy-mm-dd format. '
                             'Otherwise input \'latest\' string to get the latest, '
                             'or input \'all\' to dump all entries.',
                        **kwargs)


def add_mid_argument(parser, **kwargs):
    parser.add_argument('--mid',
                        help='Fetch specific email by a mid (message id) value.',
                        **kwargs)


def add_common_arguments(parser):
    parser.add_argument('--log-file', default='lifemotif-diem.log',
                        help='Log file path. Defaults to lifemotif-diem.log.')

    parser.add_argument('--log-level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', ],
                        default='INFO',
                        help='Log level. Defaults to INFO.')

    parser.add_argument('--timezone', default='Asia/Seoul')

    parser.add_argument('-v', '--version', action='version', version=DIEM_VERSION,
                        help='Show program version.')

# end of arguments ################################################################################################
