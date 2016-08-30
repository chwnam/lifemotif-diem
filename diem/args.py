from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os.path import expanduser

from . import DIEM_VERSION

from re import compile, IGNORECASE


def get_args():
    parser = build_parser()
    args = parser.parse_args()

    # expand ~ as home directory
    filter_arg_values(
        args=args,
        attributes=['log_file', ],
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
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    add_common_arguments(parser)

    subparsers = parser.add_subparsers(dest='subcommand')

    # authorize
    add_authorize_parser(subparsers)

    # list-label
    add_list_label_parser(subparsers)

    # create-tables
    add_create_tables_parser(subparsers)

    # drop-tables
    add_drop_tables_parser(subparsers)

    # create-profile
    add_create_profile_parser(subparsers)

    # update-database
    add_update_database_parser(subparsers)

    # rebuild-database
    add_rebuild_database_parser(subparsers)

    # query
    add_query_parser(subparsers)

    # fetch
    add_fetch_parser(subparsers)

    # fetch-incrementally
    add_fetch_incrementally_parser(subparsers)

    # fix-missing
    add_fix_missing_parser(subparsers)

    # export
    add_export_parser(subparsers)

    # message-structure
    add_message_structure_parser(subparsers)

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
def add_subparser(subparsers, parser_name, **kwargs):
    return subparsers.add_parser(parser_name, formatter_class=ArgumentDefaultsHelpFormatter, **kwargs)


def add_authorize_parser(subparsers):
    message = 'OAUTH2 authorization'
    p = add_subparser(subparsers, 'authorize', aliases=['a'], help=message, description=message)

    add_profile_path_argument(p)


def add_list_label_parser(subparsers):
    message = 'List email\'s label IDs'
    p = add_subparser(subparsers, 'list-label', aliases=['ll'], help=message, description=message)

    add_profile_path_argument(p)


def add_create_tables_parser(subparsers):
    message = 'Create database tables'
    p = add_subparser(subparsers, 'create-tables', aliases=['ct'], help=message, description=message)

    add_profile_path_argument(p)


def add_drop_tables_parser(subparsers):
    message = 'Drop database tables. Use with care!'
    p = add_subparser(subparsers, 'drop-tables', aliases=['dt'], help=message, description=message)

    add_profile_path_argument(p, required=True)
    add_force_argument(p)


def add_create_profile_parser(subparsers):
    message = 'Create a profile for Diem. A profile is required to perform any diem tasks.'
    p = add_subparser(subparsers, 'create-profile', aliases=['cp'], help=message, description=message)

    add_profile_arguments(p)


def add_update_database_parser(subparsers):
    message = 'Update database.'
    p = add_subparser(subparsers, 'update-database', aliases=['ud'], help=message, description=message)

    add_profile_path_argument(p, required=True)


def add_rebuild_database_parser(subparsers):
    message = 'Rebuild database. The same as \'drop-tables\' and \'update-database\'.'
    p = add_subparser(subparsers, 'rebuild-database', aliases=['rd'], help=message, description=message)

    add_profile_path_argument(p, required=True)
    add_force_argument(p)


def add_query_parser(subparsers):
    message = 'Query DB.'
    p = add_subparser(subparsers, 'query', aliases=['q'], help=message, description=message)

    add_profile_path_argument(p, required=True)
    add_query_string_argument(p, required=True)


def add_fetch_parser(subparsers):
    message = 'Fetch one mail.'
    p = add_subparser(subparsers, 'fetch', aliases=['f'], help=message, description=message)

    add_profile_path_argument(p, required=True)
    add_mid_argument(p, required=True, nargs='+')


def add_fetch_incrementally_parser(subparsers):
    message = 'Fetch incrementally. Update the database and fetch new reply mails.'
    p = add_subparser(subparsers, 'fetch-incrementally', aliases=['fi'], help=message, description=message)

    add_profile_path_argument(p, required=True)


def add_fix_missing_parser(subparsers):
    message = 'Fetch all reply mails that are not in archive path.'
    p = add_subparser(subparsers, 'fix-missing', aliases=['fm'], help=message, description=message)

    add_profile_path_argument(p, required=True)


def add_export_parser(subparsers):
    message = 'Export reply mail.'
    p = add_subparser(subparsers, 'export', aliases=['e'], help=message, description=message)

    add_profile_path_argument(p, required=True)
    add_mid_argument(p, required=True)
    p.add_argument('--list-converters', action='store_true')


def add_message_structure_parser(subparsers):
    message = 'Analyze and visualize message structure'
    p = add_subparser(subparsers, 'message-structure', aliases=['ms'], help=message, description=message)

    add_profile_path_argument(p, required=True)
    add_mid_argument(p, required=True)

# end of subparsers ##############################################################################################


# arguments below ################################################################################################
def add_force_argument(parser, **kwargs):
    parser.add_argument('-f', '--force', action='store_true', default=False,
                        help='Do not ask when prompting.',
                        **kwargs)


def add_query_string_argument(parser, **kwargs):
    parser.add_argument('-s', '--string', dest='query_string',
                        help='Query string. '
                             'It can be an integer, a hexadecimal, or a date string in yyyy-mm-dd format. '
                             'Otherwise input \'latest\' string to get the latest, '
                             'or input \'all\' to dump all entries.',
                        **kwargs)


def add_mid_argument(parser, **kwargs):
    parser.add_argument('-m', '--mid', help='Specify a email message id (mid) value.', **kwargs)


def add_common_arguments(parser):
    parser.add_argument('-v', '--version', action='version', version=DIEM_VERSION, help='Show program version')

    parser.add_argument('-f', '--log-file', default='./lifemotif-diem.log', help='Log file path')

    parser.add_argument('-l', '--log-level', default='INFO',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', ], help='Log level')


def add_profile_arguments(parser):
    parser.add_argument('-c', '--credential', default='./credential.json', help='Credential file path')

    parser.add_argument('-d', '--database', default='./diem.db', help='Database path')

    parser.add_argument('-s', '--storage', default='./storage.json', help='OAUTH2 token storage path')

    parser.add_argument('-e', '--email', help='Your email address')

    parser.add_argument('-k', '--label-id', help='Your target email label ID')

    parser.add_argument('-x', '--archive-path', default='archives/', help='MIME Message archive path')

    parser.add_argument('-t', '--timezone', default='UTC', help='Timezone for diary date')


def add_profile_path_argument(parser, **kwargs):
    parser.add_argument('-p', '--profile', default='./profile.json',
                        help='Profile file path. \'run.py create-profile -h\' for help', **kwargs)

# end of arguments ################################################################################################
