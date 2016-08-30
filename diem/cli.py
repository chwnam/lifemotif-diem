from collections import OrderedDict
from logging import getLogger
from json import dumps, load
from os.path import exists, expanduser
from pytz import timezone, utc
from sys import exit

from pyTree.Tree import Tree

from . import diem, get_absolute_path
from .args import get_args
from .db import open_db
from .logging import set_dict_config
from .converters import DiaryTemplateFactory

logger = getLogger(__name__)


class DiemCLI(object):
    def __init__(self):
        self.args = get_args()

        if hasattr(self.args, 'profile'):
            self.profile = self.read_profile(self.args.profile)
        else:
            self.profile = None

        set_dict_config(self.args.log_level, self.args.log_file)

        if self.profile and 'timezone' in self.profile:
            self.timezone = timezone(self.profile['timezone'])
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
        logger.debug('profile: ' + str(self.profile))

        # open database if database property is present
        if self.profile and self.profile['database']:
            conn = open_db(self.profile['database'])
        else:
            conn = None

        # subcommand process #########################################################################################

        # authorize
        if self.args.subcommand in ('authorize', 'a'):
            diem.authorize(self.profile['credential'], self.profile['storage'])

        # list-label
        elif self.args.subcommand in ('list-label', 'll'):
            for label in diem.get_labels(self.profile['storage'], self.profile['email']):
                print('%s %s' % (label['id'], label['name']))

        # create-table
        elif self.args.subcommand in ('create-tables', 'ct'):
            diem.create_tables(conn)

        # purge-tables
        elif self.args.subcommand in ('drop-tables', 'dt'):
            if self.confirm_cli('Tables will be DROPPED. Proceed?'):
                diem.drop_tables(conn)

        # create-profile
        elif self.args.subcommand in ('create-profile', 'cp'):
            self.create_profile()

        # update-structure
        elif self.args.subcommand in ('update-database', 'ud'):
            diem.update_database(
                conn=conn,
                storage=self.profile['storage'],
                email=self.profile['email'],
                label_id=self.profile['label-id']
            )

        # rebuild-structure
        elif self.args.subcommand in ('rebuild-database', 'rd'):
            if self.confirm_cli('You are going to recreate the db tables. Proceed?'):
                diem.rebuild_database(
                    conn=conn,
                    storage=self.profile['storage'],
                    email=self.profile['email'],
                    label_id=self.profile['label-id']
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
                storage=self.profile['storage'],
                email=self.profile['email'],
                archive_path=self.profile['archive-path'],
                mid_list=self.args.mid
            )

        # fetch-incrementally
        elif self.args.subcommand in ('fetch-incrementally', 'fi'):
            diem.fetch_incrementally(
                conn=conn,
                storage=self.profile['storage'],
                email=self.profile['email'],
                label_id=self.profile['label-id'],
                archive_path=self.profile['archive-path']
            )

        # fix-missing
        elif self.args.subcommand in ('fix-missing', 'fm'):
            diem.fix_missing(
                conn=conn,
                storage=self.profile['storage'],
                email=self.profile['email'],
                archive_path=self.profile['archive-path']
            )

        # export
        elif self.args.subcommand in ('export', 'e'):

            if self.args.list_converters:
                raise Exception('export --list-converters is not implemented.')
            else:
                exported = diem.export(
                    conn=conn,
                    mid=self.args.mid,
                    archive_path=self.profile['archive-path'],
                    timezone=self.timezone
                )

                print(DiaryTemplateFactory.as_json(exported, indent=2))

        # message-structure
        elif self.args.subcommand in ('message-structure', 'ms'):
            structure = diem.message_structure(self.args.mid, self.profile['archive-path'])
            self.print_message_structure(structure)

        # END of task

        if conn:
            conn.close()

    def create_profile(self):

        profile = OrderedDict()

        profile['credential'] = self.args.credential
        profile['database'] = self.args.database
        profile['storage'] = self.args.storage
        profile['email'] = self.args.email
        profile['label-id'] = self.args.label_id
        profile['archive-path'] = self.args.archive_path
        profile['timezone'] = self.args.timezone

        print(dumps(profile, indent=2))

    @staticmethod
    def read_profile(file_name):
        profile_path = get_absolute_path(file_name)

        if not exists(profile_path):
            print('Profile %s does not exist!' % file_name)
            exit(1)

        with open(profile_path, 'r') as fp:
            profile_obj = load(fp)

        for key in profile_obj:
            if key in ('credential', 'database', 'storage', 'archive-path') and len(profile_obj[key]) > 1 and \
                            profile_obj[key][0] == '~':
                profile_obj[key] = expanduser(profile_obj[key])

        return profile_obj

    @classmethod
    def print_message_structure(cls, structure):
        e = cls.message_structure_recursively(structure)
        e.prettyTree()

    @classmethod
    def message_structure_recursively(cls, structure):
        if type(structure) == dict and 'parts' in structure:
            current_node = Tree(structure['content-type'])
            for part in structure['parts']:
                entry = cls.message_structure_recursively(part)
                current_node.addChild(entry)
            return current_node
        else:
            return Tree(structure)
