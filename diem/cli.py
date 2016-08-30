from logging import getLogger

from pytz import timezone, utc

from . import diem
from .args import get_args
from .db import open_db
from .logging import set_dict_config
from .converters import DiaryTemplateFactory


logger = getLogger(__name__)


class DiemCLI(object):

    def __init__(self):
        self.args = get_args()

        set_dict_config(self.args.log_level, self.args.log_file)

        if hasattr(self.args, 'timezone'):
            self.timezone = timezone(self.args.timezone)
        else:
            self.timezone = utc

    def confirm_cli(self, message):
        if hasattr(self.args, 'force') and not self.args.force:
            i = input(message + ' [y/N] ')
            if i.lower() == 'y':
                return True
            else:
                print('canceled!')
                return False

        return True

    def run(self):

        logger.debug('arguments: ' + str(self.args))

        # open database if database property is present
        if hasattr(self.args, 'database'):
            conn = open_db(self.args.database)
        else:
            conn = None

        # subcommand process #########################################################################################

        # authorize
        if self.args.subcommand in ('authorize', 'a'):
            diem.authorize(self.args.credential, self.args.storage)

        # list-label
        elif self.args.subcommand in ('list-label', 'll'):
            for label in diem.get_labels(self.args.storage, self.args.email):
                print('%s %s' % (label['id'], label['name']))

        # create-table
        elif self.args.subcommand in ('create-tables', 'ct'):
            diem.create_tables(conn)

        # purge-tables
        elif self.args.subcommand in ('drop-tables', 'dt'):
            if self.confirm_cli('Tables will be DROPPED. Proceed?'):
                diem.drop_tables(conn)

        # update-structure
        elif self.args.subcommand in ('update-database', 'ud'):
            diem.update_database(
                conn=conn,
                storage=self.args.storage,
                email=self.args.email,
                label_id=self.args.label_id
            )

        # rebuild-structure
        elif self.args.subcommand in ('rebuild-database', 'rd'):
            if self.confirm_cli('You are going to recreate the db tables. Proceed?'):
                diem.rebuild_database(
                    conn=conn,
                    storage=self.args.storage,
                    email=self.args.email,
                    label_id=self.args.label_id
                )

        # query
        elif self.args.subcommand in ('query', 'q'):
            response = diem.query(
                conn=conn,
                query_string=self.args.query_string
            )

            if not response:
                print('No result.')
            else:
                print('MID\t\t\t\t\t\tTID\t\t\t\t\t\tDIARY DATE')
                for mid, tid, diary_date in response:
                    print('{0} (0x{0:x})\t{1} (0x{1:x})\t{2}'.format(mid, tid, diary_date, ))

        # fetch
        elif self.args.subcommand in ('fetch', 'f'):
            diem.fetch(
                storage=self.args.storage,
                email=self.args.email,
                archive_path=self.args.archive_path,
                mid_list=self.args.mid
            )

        # fetch-incrementally
        elif self.args.subcommand in ('fetch-incrementally', 'fi'):
            diem.fetch_incrementally(
                conn=conn,
                storage=self.args.storage,
                email=self.args.email,
                label_id=self.args.label_id,
                archive_path=self.args.archive_path
            )

        # fix-missing
        elif self.args.subcommand in ('fix-missing', 'fm'):
            diem.fix_missing(
                conn=conn,
                storage=self.args.storage,
                email=self.args.email,
                archive_path=self.args.archive_path
            )

        # export
        elif self.args.subcommand in ('export', 'e'):

            if self.args.list_converters:
                raise Exception('export --list-converters is not implemented.')
            else:
                exported = diem.export(
                    conn=conn,
                    mid=self.args.mid,
                    archive_path=self.args.archive_path,
                    timezone=self.timezone
                )

                print(DiaryTemplateFactory.as_json(exported, indent=2))

        if conn:
            conn.close()
